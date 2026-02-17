import argparse
import os
from datetime import datetime, timedelta, UTC

from supabase import create_client


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    try:
        if value.endswith('Z'):
            value = value[:-1] + '+00:00'
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _dedup_key(ts: datetime | None, session_id, action, page_url, project_id):
    return (
        ts.isoformat() if ts else None,
        session_id,
        action,
        page_url,
        project_id,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate legacy analytics from Supabase 'user_visits' into the app DB table 'visit_events'."
    )
    parser.add_argument('--days', type=int, default=None, help='Only migrate last N days from Supabase')
    parser.add_argument('--since', type=str, default=None, help="Only migrate records with timestamp >= this ISO value")
    parser.add_argument('--until', type=str, default=None, help="Only migrate records with timestamp <= this ISO value")
    parser.add_argument('--batch-size', type=int, default=1000, help='Supabase fetch batch size')
    parser.add_argument('--commit-size', type=int, default=500, help='DB insert commit chunk size')
    parser.add_argument('--no-dedup', action='store_true', help='Disable best-effort deduplication')
    parser.add_argument('--dry-run', action='store_true', help='Do not write anything to DB; just report counts')

    args = parser.parse_args()

    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_ANON_KEY')

    if not supabase_url or not supabase_key:
        print('❌ Missing SUPABASE_URL / SUPABASE_*_KEY environment variables')
        return 2

    try:
        sb = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f'❌ Failed to init Supabase client: {e}')
        return 2

    since_dt = None
    until_dt = None

    if args.days is not None:
        since_dt = datetime.now(UTC) - timedelta(days=max(0, args.days))

    if args.since:
        parsed = _parse_ts(args.since)
        if not parsed:
            print('❌ Invalid --since timestamp (expected ISO)')
            return 2
        since_dt = parsed

    if args.until:
        parsed = _parse_ts(args.until)
        if not parsed:
            print('❌ Invalid --until timestamp (expected ISO)')
            return 2
        until_dt = parsed

    since_iso = since_dt.isoformat() if since_dt else None
    until_iso = until_dt.isoformat() if until_dt else None

    # Import app/db only after we've validated Supabase config
    from app import app
    from models import db, VisitEvent

    existing = set()

    with app.app_context():
        if not args.no_dedup:
            try:
                q = db.session.query(
                    VisitEvent.timestamp,
                    VisitEvent.session_id,
                    VisitEvent.action,
                    VisitEvent.page_url,
                    VisitEvent.project_id,
                )
                if since_dt:
                    q = q.filter(VisitEvent.timestamp >= since_dt.replace(tzinfo=None))
                if until_dt:
                    q = q.filter(VisitEvent.timestamp <= until_dt.replace(tzinfo=None))
                for ts, session_id, action, page_url, project_id in q.all():
                    if ts and ts.tzinfo is None:
                        ts = ts.replace(tzinfo=UTC)
                    existing.add(_dedup_key(ts, session_id, action, page_url, project_id))
                print(f'Loaded {len(existing)} existing keys from DB for dedup')
            except Exception as e:
                print(f'⚠️ Dedup preload failed (continuing without dedup): {e}')
                existing.clear()

        total_fetched = 0
        total_inserted = 0
        total_skipped = 0

        start = 0
        batch_size = max(1, min(5000, args.batch_size))
        commit_size = max(1, min(5000, args.commit_size))

        pending: list[VisitEvent] = []

        while True:
            try:
                q = (
                    sb.table('user_visits')
                    .select('*')
                    .order('timestamp', desc=False)
                    .range(start, start + batch_size - 1)
                )
                if since_iso:
                    q = q.gte('timestamp', since_iso)
                if until_iso:
                    q = q.lte('timestamp', until_iso)
                res = q.execute()
                rows = res.data or []
            except Exception as e:
                print(f'❌ Supabase fetch failed at range {start}-{start + batch_size - 1}: {e}')
                return 3

            if not rows:
                break

            total_fetched += len(rows)

            for row in rows:
                ts = _parse_ts(row.get('timestamp'))
                if ts and ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)

                action = row.get('action') or 'page_view'
                session_id = row.get('session_id')
                page_url = row.get('page_url')
                project_id = row.get('project_id')

                if not args.no_dedup:
                    key = _dedup_key(ts, session_id, action, page_url, project_id)
                    if key in existing:
                        total_skipped += 1
                        continue
                    existing.add(key)

                evt = VisitEvent(
                    timestamp=(ts.replace(tzinfo=None) if ts else None),
                    session_id=session_id,
                    user_id=row.get('user_id'),
                    ip_address=row.get('ip_address') or row.get('ip'),
                    user_agent=row.get('user_agent'),
                    page_url=page_url,
                    referrer=row.get('referrer'),
                    screen_resolution=row.get('screen_resolution'),
                    action=action,
                    project_id=str(project_id) if project_id not in (None, '') else None,
                )
                pending.append(evt)

                if len(pending) >= commit_size:
                    if not args.dry_run:
                        try:
                            db.session.bulk_save_objects(pending)
                            db.session.commit()
                        except Exception as e:
                            db.session.rollback()
                            print(f'❌ DB commit failed: {e}')
                            return 4
                    total_inserted += len(pending)
                    pending.clear()

            if len(rows) < batch_size:
                break
            start += batch_size

        if pending:
            if not args.dry_run:
                try:
                    db.session.bulk_save_objects(pending)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f'❌ DB commit failed: {e}')
                    return 4
            total_inserted += len(pending)
            pending.clear()

        print('✅ Migration complete')
        print(f'  Fetched from Supabase: {total_fetched}')
        print(f'  Inserted into DB:      {total_inserted}' + (' (dry-run)' if args.dry_run else ''))
        print(f'  Skipped (dedup):       {total_skipped}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

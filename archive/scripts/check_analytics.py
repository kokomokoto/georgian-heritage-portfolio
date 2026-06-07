import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_ANON_KEY')

if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
        print('Supabase connection successful')

        # Check current record count
        result = supabase.table('user_visits').select('count', count='exact').execute()
        print(f'Current record count: {result.count}')

        if result.count > 0:
            # Get recent visits
            recent = supabase.table('user_visits').select('*').order('timestamp', desc=True).limit(5).execute()
            print(f'Recent visits: {len(recent.data)} records')
            for visit in recent.data[:3]:  # Show only first 3
                print(f'  - {visit["page_url"]} (IP: {visit["ip_address"]})')

    except Exception as e:
        print(f'Error: {e}')
else:
    print('Supabase credentials not found')
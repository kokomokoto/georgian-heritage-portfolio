import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
import uuid

load_dotenv()

supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_ANON_KEY')

if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
        print('Supabase connected')

        # Simulate what the API does
        session_id = str(uuid.uuid4())
        ip_address = None  # Simulating local development
        user_agent = 'Test Browser'
        page_url = 'http://localhost:5002/'
        screen_resolution = '1920x1080'
        referrer = None
        timestamp = datetime.utcnow().isoformat()
        user_id = None
        action = 'page_view'

        visit_data = {
            'session_id': session_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'page_url': page_url,
            'screen_resolution': screen_resolution,
            'referrer': referrer,
            'timestamp': timestamp,
            'user_id': user_id,
            'action': action
        }

        print(f'Inserting data: {visit_data}')

        result = supabase.table('user_visits').insert(visit_data).execute()
        print('SUCCESS: Data inserted!')
        print(f'Result: {result}')

    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()
else:
    print('Credentials not found')
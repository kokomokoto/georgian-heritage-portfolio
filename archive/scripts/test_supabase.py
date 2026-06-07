#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase Connection Test Script
ტესტირების სკრიპტი Supabase კავშირის შესამოწმებლად
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import supabase

def test_supabase_connection():
    """ტესტირება Supabase კავშირის"""
    print("🔍 ტესტირება Supabase კავშირის...")

    if not supabase:
        print("❌ Supabase კლიენტი არ არის ინიციალიზებული")
        print("💡 შეამოწმეთ .env ფაილი SUPABASE_URL და SUPABASE_ANON_KEY ცვლადებისთვის")
        return False

    try:
        # ტესტირება ცხრილის არსებობის
        result = supabase.table('user_visits').select('id').limit(1).execute()
        print("✅ user_visits ცხრილი არსებობს")

        # ტესტირება მონაცემების ჩაწერის
        test_data = {
            'session_id': 'test-session-123',
            'ip_address': '127.0.0.1',
            'user_agent': 'Test Script',
            'page_url': '/test',
            'screen_resolution': '1920x1080',
            'action': 'test'
        }

        insert_result = supabase.table('user_visits').insert(test_data).execute()
        print("✅ მონაცემების ჩაწერა წარმატებულია")

        # ტესტირება მონაცემების წაკითხვის
        select_result = supabase.table('user_visits').select('*').eq('session_id', 'test-session-123').execute()
        if select_result.data:
            print("✅ მონაცემების წაკითხვა წარმატებულია")
        else:
            print("⚠️ მონაცემები არ მოიძებნა")

        # ტესტირება მონაცემების წაშლის (წმენდა)
        delete_result = supabase.table('user_visits').delete().eq('session_id', 'test-session-123').execute()
        print("✅ ტესტის მონაცემები წაშლილია")

        print("\n🎉 Supabase კავშირი მუშაობს სრულად!")
        return True

    except Exception as e:
        print(f"❌ შეცდომა Supabase ტესტირებისას: {e}")
        print("\n🔧 შესაძლო გადაწყვეტილებები:")
        print("1. შეამოწმეთ SUPABASE_URL და SUPABASE_ANON_KEY .env ფაილში")
        print("2. გაუშვით supabase_schema.sql Supabase SQL Editor-ში")
        print("3. შეამოწმეთ ინტერნეტ კავშირი")
        return False

def test_tracking_function():
    """ტესტირება track_user_visit ფუნქციის"""
    print("\n🔍 ტესტირება track_user_visit ფუნქციის...")

    try:
        from app import track_user_visit

        result = track_user_visit(
            page_url='/test-page',
            user_agent='Test Browser',
            screen_resolution='1920x1080'
        )

        if result:
            print("✅ track_user_visit ფუნქცია მუშაობს")
            return True
        else:
            print("❌ track_user_visit ფუნქცია ვერ შესრულდა")
            return False

    except Exception as e:
        print(f"❌ შეცდომა track_user_visit ტესტირებისას: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Supabase მომხმარებელთა მონიტორინგის ტესტირება\n")

    # ტესტირება Supabase კავშირის
    supabase_ok = test_supabase_connection()

    # ტესტირება ტრეკინგ ფუნქციის
    tracking_ok = test_tracking_function()

    print("\n" + "="*50)
    if supabase_ok and tracking_ok:
        print("🎉 ყველა ტესტი წარმატებით გავიდა!")
        print("მომხმარებელთა მონიტორინგი მზადაა გამოსაყენებლად")
    else:
        print("❌ ზოგიერთი ტესტი ვერ გავიდა")
        print("გთხოვთ შეამოწმოთ კონფიგურაცია SUPABASE_SETUP.md-ში")

    sys.exit(0 if (supabase_ok and tracking_ok) else 1)
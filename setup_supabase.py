#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Supabase Setup Script
სწრაფი დაყენების სკრიპტი Supabase-სთვის
"""
import os
import sys

def create_env_file():
    """შექმნის .env ფაილს თუ არ არსებობს"""
    env_path = '.env'

    if os.path.exists(env_path):
        print(f"✅ .env ფაილი უკვე არსებობს: {env_path}")
        return True

    try:
        # დააკოპირეთ .env.example
        example_path = '.env.example'
        if os.path.exists(example_path):
            with open(example_path, 'r', encoding='utf-8') as src:
                content = src.read()

            with open(env_path, 'w', encoding='utf-8') as dst:
                dst.write(content)

            print(f"✅ შეიქმნა .env ფაილი {env_path}-ში")
            print("📝 გთხოვთ შეავსოთ SUPABASE_URL და SUPABASE_ANON_KEY")
            return True
        else:
            print("❌ .env.example ფაილი არ მოიძებნა")
            return False

    except Exception as e:
        print(f"❌ შეცდომა .env ფაილის შექმნისას: {e}")
        return False

def check_supabase_schema():
    """შეამოწმებს supabase_schema.sql ფაილის არსებობა"""
    schema_path = 'supabase_schema.sql'

    if os.path.exists(schema_path):
        print(f"✅ SQL სქემის ფაილი არსებობს: {schema_path}")
        print("📋 გთხოვთ გაუშვათ ეს ფაილი Supabase SQL Editor-ში")
        return True
    else:
        print(f"❌ SQL სქემის ფაილი არ მოიძებნა: {schema_path}")
        return False

def print_setup_instructions():
    """დაბეჭდავს დაყენების ინსტრუქციებს"""
    print("\n" + "="*60)
    print("🚀 SUPABASE დაყენების ინსტრუქციები")
    print("="*60)

    print("\n1️⃣ შექმენით Supabase ანგარიში:")
    print("   📍 გადადით: https://supabase.com")
    print("   📝 შექმენით ახალი პროექტი")

    print("\n2️⃣ გაუშვით მონაცემთა ბაზის სქემა:")
    print("   📍 გადადით SQL Editor-ში")
    print("   📋 დააკოპირეთ და ჩასვით supabase_schema.sql-ის შინაარსი")
    print("   ▶️ დააჭირეთ 'Run'")

    print("\n3️⃣ მიიღეთ API გასაღებები:")
    print("   📍 Settings → API")
    print("   📋 დააკოპირეთ Project URL და anon key")

    print("\n4️⃣ დააკონფიგურირეთ .env ფაილი:")
    print("   📝 შეავსეთ SUPABASE_URL და SUPABASE_ANON_KEY")

    print("\n5️⃣ გადატვირთეთ აპლიკაცია:")
    print("   🔄 python app.py")

    print("\n6️⃣ ტესტირება:")
    print("   🧪 python test_supabase.py")

    print("\n7️⃣ შეამოწმეთ ანალიტიკა:")
    print("   📊 გადადით: /admin/analytics")

    print("\n" + "="*60)
    print("📖 დეტალური ინსტრუქციები: SUPABASE_SETUP.md")
    print("="*60)

def main():
    """მთავარი ფუნქცია"""
    print("🔧 Supabase სწრაფი დაყენების სკრიპტი\n")

    # შექმენით .env ფაილი
    env_ok = create_env_file()

    # შეამოწმეთ SQL სქემა
    schema_ok = check_supabase_schema()

    # დაბეჭდეთ ინსტრუქციები
    print_setup_instructions()

    print("\n" + "="*60)
    if env_ok and schema_ok:
        print("✅ დაყენების ფაილები მზადაა!")
        print("📋 მიჰყევით ზემოთ მოცემულ ინსტრუქციებს")
    else:
        print("❌ ზოგიერთი ფაილი არ მოიძებნა")
        print("📋 შეამოწმეთ პროექტის სტრუქტურა")
    print("="*60)

if __name__ == "__main__":
    main()
"""
Database Connection Test Script
Run this to verify your Supabase database is properly configured
"""
import sys
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

print("🧪 Testing Database Connection...\n")
print("=" * 60)

# Check if environment variables are loaded
print("\n1️⃣ Checking Environment Variables...")
required_vars = [
    "DATABASE_URL",
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "OPENAI_API_KEY"
]

missing_vars = []
for var in required_vars:
    value = os.getenv(var)
    if not value:
        print(f"   ❌ {var} is missing!")
        missing_vars.append(var)
    else:
        # Show first 20 chars only for security
        masked = value[:20] + "..." if len(value) > 20 else value
        print(f"   ✅ {var} = {masked}")

if missing_vars:
    print(f"\n❌ Missing variables: {', '.join(missing_vars)}")
    print("Please check your .env file!")
    sys.exit(1)

print("\n✅ All required environment variables found!")

# Test database connection
print("\n2️⃣ Testing Database Connection...")
try:
    import psycopg
    from psycopg.rows import dict_row
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            # Test basic query
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"   ✅ Connected to PostgreSQL!")
            print(f"   📊 Version: {version['version'][:50]}...")
            
except Exception as e:
    print(f"   ❌ Connection failed: {str(e)}")
    print("\n💡 Tips:")
    print("   - Check your DATABASE_URL in .env")
    print("   - Make sure password is correct")
    print("   - Verify you're using port 6543 (connection pooler)")
    sys.exit(1)

# Test tables exist
print("\n3️⃣ Checking Database Tables...")
try:
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            # Get all tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            
            expected_tables = [
                'assets', 'brand_assets', 'brand_kits', 'jobs',
                'organizations', 'plans', 'subscriptions', 'usage', 'users'
            ]
            
            table_names = [t['table_name'] for t in tables]
            
            print(f"   📋 Found {len(table_names)} tables:")
            for table in expected_tables:
                if table in table_names:
                    print(f"      ✅ {table}")
                else:
                    print(f"      ❌ {table} (missing!)")
            
            missing_tables = [t for t in expected_tables if t not in table_names]
            if missing_tables:
                print(f"\n   ⚠️ Missing tables: {', '.join(missing_tables)}")
                print("   💡 Run schema.sql in Supabase SQL Editor")
            else:
                print("\n   ✅ All tables exist!")
                
except Exception as e:
    print(f"   ❌ Error checking tables: {str(e)}")
    sys.exit(1)

# Test seed data
print("\n4️⃣ Checking Seed Data...")
try:
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            # Check organizations
            cur.execute("SELECT COUNT(*) as count FROM organizations;")
            org_count = cur.fetchone()['count']
            print(f"   📊 Organizations: {org_count}")
            
            # Check users
            cur.execute("SELECT COUNT(*) as count FROM users;")
            user_count = cur.fetchone()['count']
            print(f"   👥 Users: {user_count}")
            
            # Check plans
            cur.execute("SELECT COUNT(*) as count FROM plans;")
            plan_count = cur.fetchone()['count']
            print(f"   💳 Plans: {plan_count}")
            
            # Check brand_kits
            cur.execute("SELECT COUNT(*) as count FROM brand_kits;")
            kit_count = cur.fetchone()['count']
            print(f"   🎨 Brand Kits: {kit_count}")
            
            if org_count > 0 and user_count > 0 and plan_count > 0:
                print("\n   ✅ Seed data loaded successfully!")
            else:
                print("\n   ⚠️ Seed data might be missing")
                print("   💡 Run seed.sql in Supabase SQL Editor")
                
except Exception as e:
    print(f"   ❌ Error checking seed data: {str(e)}")

# Test Supabase client
print("\n5️⃣ Testing Supabase Client...")
try:
    from supabase import create_client, Client
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Test a simple query
    response = supabase.table("organizations").select("*").limit(1).execute()
    
    print(f"   ✅ Supabase client working!")
    print(f"   📊 Can query tables via Supabase SDK")
    
except Exception as e:
    print(f"   ❌ Supabase client error: {str(e)}")
    print("   💡 Check SUPABASE_URL and SUPABASE_KEY in .env")

# Test OpenAI
print("\n6️⃣ Testing OpenAI API...")
try:
    from openai import OpenAI
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Test with a simple models list call (doesn't cost anything)
    models = client.models.list()
    print(f"   ✅ OpenAI API key is valid!")
    print(f"   🤖 Can access OpenAI services")
    
except Exception as e:
    print(f"   ❌ OpenAI API error: {str(e)}")
    print("   💡 Check OPENAI_API_KEY in .env")
    print("   💡 Get your key from: https://platform.openai.com/api-keys")

# Final summary
print("\n" + "=" * 60)
print("\n🎉 Connection Test Complete!\n")
print("✅ Your environment is ready for development!")
print("\n💡 Next steps:")
print("   1. We'll build the core engine modules")
print("   2. Create the Streamlit pages")
print("   3. Test the full workflow")
print("\n" + "=" * 60)
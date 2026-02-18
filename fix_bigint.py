import psycopg2
import urllib.parse
import sys

# PASTE YOUR DATABASE URL HERE
DATABASE_URL = "postgresql://mealbot_user:6BlxC5h7UT9ArcdNsTbbUgUIMyKJSZl5@dpg-d69b24gboq4c73ddjog0-a.oregon-postgres.render.com/mealbot_db_mnif"  # Replace with your URL from Render

try:
    # Parse connection string
    parsed = urllib.parse.urlparse(DATABASE_URL)
    db_config = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/')
    }

    print("🔧 Connecting to database...")
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    print("✅ Connected!\n")

    # Migration commands
    commands = [
        "ALTER TABLE users ALTER COLUMN id TYPE BIGINT;",
        "ALTER TABLE meal_logs ALTER COLUMN user_id TYPE BIGINT;",
        "ALTER TABLE meal_plans ALTER COLUMN user_id TYPE BIGINT;",
        "ALTER TABLE daily_summary ALTER COLUMN user_id TYPE BIGINT;",
        "ALTER TABLE activity_logs ALTER COLUMN user_id TYPE BIGINT;",
        "ALTER TABLE user_preferences ALTER COLUMN user_id TYPE BIGINT;",
    ]

    print("Running migration...\n")

    for cmd in commands:
        try:
            print(f"Executing: {cmd}")
            cursor.execute(cmd)
            conn.commit()
            print("✅ Success\n")
        except Exception as e:
            conn.rollback()
            print(f"❌ Error: {e}\n")

    # Verify
    print("Verifying changes...\n")
    cursor.execute("""
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE column_name LIKE '%id%' AND data_type IN ('integer', 'bigint')
        ORDER BY table_name, column_name;
    """)

    print("📋 Results:")
    results = cursor.fetchall()
    for row in results:
        print(f"  {row[0]}.{row[1]}: {row[2]}")

    if all(row[2] == 'bigint' for row in results):
        print("\n✅ All columns are now BIGINT!")
    else:
        print("\n⚠️ Some columns are still INTEGER")

    cursor.close()
    conn.close()
    print("\n✅ Migration complete!")

except Exception as e:
    print(f"❌ Fatal error: {e}")
    sys.exit(1)
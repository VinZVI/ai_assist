import asyncio
import asyncpg


async def check_db():
    try:
        # Connect to the database
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="3245",
            database="ai_assist",
        )

        # Check if the age_verified column exists
        columns = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'age_verified'
        """)

        print(f"age_verified column exists: {len(columns) > 0}")

        # Get all columns in the users table
        all_columns = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)

        print("All user columns:")
        for col in all_columns:
            print(f"  - {col['column_name']}")

        await conn.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(check_db())

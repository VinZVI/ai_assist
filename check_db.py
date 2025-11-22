from app.database import engine
import asyncio

async def check_tables():
    async with engine.connect() as conn:
        # Check if age_verified column exists
        result = await conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'age_verified';"
        )
        rows = result.fetchall()
        print('age_verified column exists:', len(rows) > 0)
        
        # Check applied migrations
        try:
            result = await conn.execute('SELECT version_num FROM alembic_version;')
            rows = result.fetchall()
            print('Applied migrations:', [row[0] for row in rows])
        except Exception as e:
            print('Error checking migrations:', e)
        
        # List all user columns
        result = await conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'users';"
        )
        rows = result.fetchall()
        print('All user columns:', [row[0] for row in rows])

if __name__ == "__main__":
    asyncio.run(check_tables())
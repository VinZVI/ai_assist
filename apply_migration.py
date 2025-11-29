import asyncio

import asyncpg


async def apply_migration():
    try:
        # Connect to the database
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="3245",
            database="ai_assist",
        )

        # Apply the migration SQL commands
        migration_sql = [
            # Create enum type for verification_status
            "CREATE TYPE verification_status AS ENUM ('pending', 'verified', 'rejected', 'expired');",
            # Add new columns to users table
            "ALTER TABLE users ADD COLUMN age_verified BOOLEAN NOT NULL DEFAULT false;",
            "ALTER TABLE users ADD COLUMN terms_accepted BOOLEAN NOT NULL DEFAULT false;",
            "ALTER TABLE users ADD COLUMN privacy_policy_accepted BOOLEAN NOT NULL DEFAULT false;",
            "ALTER TABLE users ADD COLUMN community_guidelines_accepted BOOLEAN NOT NULL DEFAULT false;",
            "ALTER TABLE users ADD COLUMN consent_timestamp TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE users ADD COLUMN consent_ip_address VARCHAR(45);",
            "ALTER TABLE users ADD COLUMN terms_version VARCHAR(10);",
            "ALTER TABLE users ADD COLUMN privacy_version VARCHAR(10);",
            "ALTER TABLE users ADD COLUMN guidelines_version VARCHAR(10);",
            "ALTER TABLE users ADD COLUMN verification_status verification_status NOT NULL DEFAULT 'pending';",
        ]

        for sql in migration_sql:
            try:
                await conn.execute(sql)
                print(f"Executed: {sql[:50]}...")
            except Exception as e:
                print(f"Skipped (might already exist): {sql[:50]}... - {e}")

        await conn.close()
        print("Migration applied successfully!")

    except Exception as e:
        print(f"Error applying migration: {e}")


if __name__ == "__main__":
    asyncio.run(apply_migration())

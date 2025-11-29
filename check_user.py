import asyncio

import asyncpg


async def check_user():
    try:
        # Connect to the database
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="3245",
            database="ai_assist",
        )

        # Check the user data
        user_data = await conn.fetchrow(
            """
            SELECT id, telegram_id, age_verified, terms_accepted, privacy_policy_accepted, 
                   community_guidelines_accepted, verification_status
            FROM users 
            WHERE telegram_id = $1
        """,
            467055923,
        )

        if user_data:
            print("User data:")
            print(f"  ID: {user_data['id']}")
            print(f"  Telegram ID: {user_data['telegram_id']}")
            print(f"  Age verified: {user_data['age_verified']}")
            print(f"  Terms accepted: {user_data['terms_accepted']}")
            print(f"  Privacy policy accepted: {user_data['privacy_policy_accepted']}")
            print(
                f"  Community guidelines accepted: {user_data['community_guidelines_accepted']}"
            )
            print(f"  Verification status: {user_data['verification_status']}")
            print(
                f"  Is fully verified: {user_data['age_verified'] and user_data['terms_accepted'] and user_data['privacy_policy_accepted'] and user_data['community_guidelines_accepted'] and user_data['verification_status'] == 'verified'}"
            )
        else:
            print("User not found in database")

        await conn.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(check_user())

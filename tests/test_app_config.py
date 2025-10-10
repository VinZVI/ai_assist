"""
Test script to verify that AppConfig has the admin field.
"""

from app.config import get_config


def test_app_config_has_admin_field():
    """Test that AppConfig has the admin field."""
    config = get_config()
    print(f"Config type: {type(config)}")
    print(f"Config attributes: {dir(config)}")
    
    # Check if admin field exists
    if hasattr(config, 'admin'):
        print("✅ AppConfig has admin field")
        print(f"Admin config type: {type(config.admin)}")
        print(f"Admin user ID: {config.admin.admin_user_id}")
        admin_ids = config.admin.get_admin_ids()
        print(f"Admin IDs: {admin_ids}")
    else:
        print("❌ AppConfig does not have admin field")
        print("Available attributes:")
        for attr in dir(config):
            if not attr.startswith('_'):
                print(f"  {attr}")


if __name__ == "__main__":
    test_app_config_has_admin_field()
from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings

class TestConfig(BaseSettings):
    field1: str = Field(default='default', env='FIELD1')
    field2: str = Field(default='default2', env='FIELD2')
    computed_field: str | None = Field(default=None, env='COMPUTED_FIELD')

    @field_validator("computed_field", mode="before")
    @classmethod
    def build_computed_field(cls, v: str | None, info: ValidationInfo) -> str:
        """Build computed field from other fields."""
        print(f"Validator called with v={v}, info.data={info.data}")
        
        if v is not None:
            return v

        # Get values from info.data if available
        values = info.data if hasattr(info, "data") else {}
        field1 = values.get("field1", "default")
        field2 = values.get("field2", "default2")

        return f"{field1}_{field2}"

# Test 1: With constructor parameters
print("=== Test 1: Constructor parameters ===")
try:
    config1 = TestConfig(field1='test', field2='test2')
    print(f"field1: {config1.field1}")
    print(f"field2: {config1.field2}")
    print(f"computed_field: {config1.computed_field}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: With environment variables
print("\n=== Test 2: Environment variables ===")
import os
os.environ['FIELD1'] = 'env_test'
os.environ['FIELD2'] = 'env_test2'

try:
    config2 = TestConfig()
    print(f"field1: {config2.field1}")
    print(f"field2: {config2.field2}")
    print(f"computed_field: {config2.computed_field}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Mixed (constructor overrides env)
print("\n=== Test 3: Mixed (constructor overrides env) ===")
try:
    config3 = TestConfig(field1='constructor_override')
    print(f"field1: {config3.field1}")
    print(f"field2: {config3.field2}")
    print(f"computed_field: {config3.computed_field}")
except Exception as e:
    print(f"Error: {e}")
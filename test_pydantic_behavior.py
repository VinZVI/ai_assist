import contextlib

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings


class TestConfig(BaseSettings):
    field1: str = Field(default="default")
    field2: str = Field(default="default2")
    computed_field: str | None = Field(default=None)

    model_config = {"extra": "allow"}

    @field_validator("computed_field", mode="before")
    @classmethod
    def build_computed_field(cls, v: str | None, info: ValidationInfo) -> str:
        """Build computed field from other fields."""

        if v is not None:
            return v

        # Get values from info.data if available
        values = info.data if hasattr(info, "data") else {}
        field1 = values.get("field1", "default")
        field2 = values.get("field2", "default2")

        return f"{field1}_{field2}"


# Test 1: With constructor parameters
with contextlib.suppress(Exception):
    config1 = TestConfig(field1="test", field2="test2")

# Test 2: With environment variables
import contextlib
import os

os.environ["FIELD1"] = "env_test"
os.environ["FIELD2"] = "env_test2"

with contextlib.suppress(Exception):
    config2 = TestConfig()

# Test 3: Mixed (constructor overrides env)
with contextlib.suppress(Exception):
    config3 = TestConfig(field1="constructor_override")

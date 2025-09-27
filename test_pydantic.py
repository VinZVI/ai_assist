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


config = TestConfig(field1="test", field2="test2")
print("field1:", config.field1)
print("field2:", config.field2)
print("computed_field:", config.computed_field)

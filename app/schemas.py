from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=1, repr=False)

    @field_validator("email")
    @classmethod
    def email_fits_database(cls, value: str) -> str:
        if len(value) > 100:
            raise ValueError("Email must be at most 100 characters")
        return value


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    created_at: datetime | None

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from custom_types import Lower


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: Lower[EmailStr] = Field(max_length=120)

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: Lower[EmailStr] | None= Field(default=None, max_length=120)

class UserPrivate(BaseModel):
    id: int
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr

class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    
    model_config = ConfigDict(from_attributes=True)

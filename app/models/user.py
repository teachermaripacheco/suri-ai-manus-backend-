from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDBBase(UserBase):
    id: str # Assuming Firebase User ID is a string

    class Config:
        from_attributes = True # Replaces orm_mode = True in Pydantic v2

# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str # We won't return this normally

# Properties to return to client
class UserPublic(UserInDBBase):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: EmailStr | None = None


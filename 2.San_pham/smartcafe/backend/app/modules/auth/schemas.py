from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class BranchBrief(BaseModel):
    id: int
    code: str
    name: str


class StaffMe(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    branch: BranchBrief | None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    staff: StaffMe

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Annotated

class MemberInfo(BaseModel):
    uid: str
    name: str
    foodName: Optional[str] = None
    price: Optional[int] = None
    status: Optional[int] = None

# --- User ---
# signup
class UserSignupCreate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=50, description="暱稱")]
    mail: Annotated[str, Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="信箱格式")]
    password: Annotated[str, Field(min_length=8, max_length=100, description="密碼至少 8 碼")]

class UserSignupResponse(BaseModel):
    uid: str
    class Config:
        from_attributes = True

# login
class UserLogin(BaseModel):
    mail: Annotated[str, Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="信箱格式")]
    password: Annotated[str, Field(min_length=8, max_length=100, description="密碼至少 8 碼")]

class UserLoginResponse(BaseModel):
    uid: str
    name: str
    class Config:
        from_attributes = True

# get user data
class ActivityInfo(BaseModel):
    type: str
    title: str
    date: str
    status: str

class GetUser(BaseModel):
    uid: str
    name: str
    mail: str
    history: Optional[List[ActivityInfo]] = None

    class Config:
        from_attributes = True

# patch user data
class UserChange(BaseModel):
    name: Annotated[Optional[str], Field(min_length=1, max_length=50, default=None)]
    mail: Annotated[Optional[str], Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", default=None)]
    password: Annotated[Optional[str], Field(min_length=8, max_length=100, default=None)]

# delete user data
class DeleteUser(BaseModel):
    uid: str
    password: str

# --- Team ---
# create team
class TeamCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=100, description="揪團標題")]
    url: Annotated[str, Field(pattern=r"^https?://.*", description="必須是有效的網址")]
    location: Annotated[str, Field(min_length=1, max_length=100, description="面交地點")]
    deliverFee: Annotated[int, Field(ge=0, description="運費不可為負數")]
    endAt: datetime
    description: Annotated[Optional[str], Field(max_length=500, default=None)]

class TeamResponse(BaseModel):
    orderId: str
    ownerId: str
    ownerName: Optional[str] = None
    title: str
    url: str
    location: str
    deliverFee: int
    endAt: datetime
    description: Optional[str]=None
    member: Optional[List[MemberInfo]]=None
    joinRequests: Optional[List[MemberInfo]]=None
    memberNum: Optional[int]=None
    totalPrice: Optional[int]=None

    class Config:
        from_attributes = True

# --- JoinTeam ---
# join
class JoinTeamCreate(BaseModel):
    foodName: Annotated[str, Field(min_length=1, max_length=100, description="餐點名稱")]
    price: Annotated[int, Field(ge=0, description="價格不可為負數")]

class JoinTeamResponse(BaseModel):
    orderId: str
    uid: str
    name: str
    foodName: str
    status: int
    price: int

    class Config:
        from_attributes = True

class HandleJoinTeam(BaseModel):
    status: Annotated[int, Field(ge=0, le=3, description="狀態碼")]

class HandleResponse(BaseModel):
    orderId: str
    uid: str
    status: int

    class Config:
        from_attributes = True

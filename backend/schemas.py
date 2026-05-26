from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class MemberInfo(BaseModel):
    uid: str
    name: str

# --- User ---
# signup
class UserSignupCreate(BaseModel):
    name: str
    mail: str
    password: str

class UserSignupResponse(BaseModel):
    uid: str
    class Config:
        from_attributes = True

# login
class UserLogin(BaseModel):
    mail: str
    password: str

class UserLoginResponse(BaseModel):
    uid: str
    name: str
    class Config:
        from_attributes = True

# get user data
class GetUser(BaseModel):
    uid: str
    name: str
    mainImage: Optional[str]=None
    mail: str

    class Config:
        from_attributes = True

# patch user data
class UserChange(BaseModel):
    name: Optional[str]=None
    mainImage: Optional[str]=None
    mail: Optional[str]=None
    password: Optional[str]=None

# delete user data
class DeleteUser(BaseModel):
    uid: str
    password: str

# --- Team ---
# create team
class TeamCreate(BaseModel):
    title: str
    url: str
    location: str
    deliverFee: int
    endAt: datetime
    description: Optional[str]=None

class TeamResponse(BaseModel):
    orderId: str
    ownerId: str
    title: str
    url: str
    location: str
    deliverFee: int
    endAt: datetime
    description: Optional[str]=None
    member: Optional[List[MemberInfo]]=None
    memberNum: Optional[int]=None
    totalPrice: Optional[int]=None

    class Config:
        from_attributes = True

# --- JoinTeam ---
# join
class JoinTeamCreate(BaseModel):
    foodName: str
    price: int

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
    status: int

class HandleResponse(BaseModel):
    orderId: str
    uid: str
    status: int

    class Config:
        from_attributes = True
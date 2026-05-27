import uuid
from fastapi import FastAPI, Depends, HTTPException, Cookie
import os
import secrets
from datetime import datetime, timedelta
import jwt
from sqlalchemy.orm import Session
from schemas import (UserSignupCreate, UserSignupResponse, UserLogin, UserLoginResponse
, GetUser, UserChange, DeleteUser, TeamCreate, TeamResponse, JoinTeamCreate
, JoinTeamResponse, HandleJoinTeam, HandleResponse, MemberInfo)
from database import SessionLocal, Base, engine
from models import User, Team, JoinTeam, RefreshToken
from fastapi.responses import JSONResponse
from typing import List
from fastapi.staticfiles import StaticFiles

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# JWT / token settings
JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_EXPIRE_DAYS", "7"))

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
    return encoded_jwt

# sign up = add user
@app.post("/api/account/signup", response_model=UserSignupResponse)
def addAccount(user: UserSignupCreate, db: Session = Depends(get_db)):
    uid = str(uuid.uuid4())
    new_user = User(uid=uid, mail=user.mail, name=user.name, hashed_password=user.password)
    db.add(new_user)
    db.commit()
    return {"uid": uid}

# log in
@app.post("/api/account/login", response_model=UserLoginResponse)
def loginAccount(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.mail == user.mail).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    if user.password != db_user.hashed_password:
        raise HTTPException(status_code=401, detail="帳號密碼錯誤")
    else:
        # 成功登入：產生 access token 與 refresh token，並把 refresh token 存入 DB
        access_token = create_access_token({"sub": db_user.uid, "name": db_user.name})
        refresh_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        db_refresh = RefreshToken(token=refresh_token, uid=db_user.uid, expires_at=expires_at)
        db.add(db_refresh)
        db.commit()

        resp = JSONResponse(content={"access_token": access_token, "token_type": "bearer", "uid": db_user.uid, "name": db_user.name})
        resp.set_cookie("refresh_token", refresh_token, httponly=True, samesite="lax", max_age=REFRESH_TOKEN_EXPIRE_DAYS*24*3600, path="/")
        return resp

@app.post("/api/account/logout")
def logout(refresh_token: str = Cookie(None), db: Session = Depends(get_db)):
    # 刪除儲存在資料庫中的 refresh token（如果有）並清除 cookie
    if refresh_token:
        db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
        if db_token:
            db.delete(db_token)
            db.commit()
    resp = JSONResponse(content={})
    resp.delete_cookie("refresh_token", path="/")
    return resp


@app.post("/api/account/refresh")
def refresh_access_token(refresh_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="缺少 refresh token")
    db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not db_token:
        raise HTTPException(status_code=401, detail="無效的 refresh token")
    if db_token.expires_at and db_token.expires_at < datetime.utcnow():
        # expired: 移除並拒絕
        db.delete(db_token)
        db.commit()
        raise HTTPException(status_code=401, detail="refresh token 已過期")
    db_user = db.query(User).filter(User.uid == db_token.uid).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    access_token = create_access_token({"sub": db_user.uid, "name": db_user.name})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/account/{uid}", response_model=GetUser)
def getUserData(uid: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.uid == uid).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    else:
        return {"uid": db_user.uid, "name": db_user.name, "mail": db_user.mail, "mainImage": db_user.mainImage}

@app.patch("/api/account/{uid}", response_model=GetUser)
def changeUserData(uid: str, user: UserChange, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.uid == uid).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    else:
        if user.name:
            db_user.name = user.name
        if user.mail:
            db_user.mail = user.mail
        if user.password:
            db_user.hashed_password = user.password
        if user.mainImage:
            db_user.mainImage = user.mainImage
        db.commit()
        return {"uid": db_user.uid, "name": db_user.name, "mail": db_user.mail, "mainImage": db_user.mainImage}

@app.delete("/api/account/{uid}")
def deleteUser(uid: str, password: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.uid == uid).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    elif db_user.hashed_password != password:
        raise HTTPException(status_code=401, detail="密碼輸入錯誤")
    else:
        db.delete(db_user)
        db.commit()
        return {}

@app.post("/api/team", response_model=TeamResponse)
def createTeam(uid: str, team: TeamCreate, db: Session = Depends(get_db)):
    orderId = str(uuid.uuid4())
    new_team = Team(orderId=orderId, ownerId=uid, url=team.url, title=team.title, location=team.location, deliverFee=team.deliverFee, endAt=team.endAt, description=team.description)
    db.add(new_team)
    db.commit()
    return {
                "orderId": new_team.orderId,
                "ownerId": new_team.ownerId,
                "title": new_team.title,
                "url": new_team.url,
                "location": new_team.location,
                "deliverFee": new_team.deliverFee,
                "endAt": new_team.endAt,
                "description": new_team.description,
                "member": [],
                "memberNum": 0,
                "totalPrice": 0
            }
@app.get("/api/team", response_model=List[TeamResponse])
def getTeam(db: Session = Depends(get_db)):
    db_teamlist = db.query(Team).all()
    result = []

    for db_team in db_teamlist:
        members = db.query(JoinTeam).filter(
            JoinTeam.orderId == db_team.orderId,
            JoinTeam.status == 1
        ).all()
        member_list = []
        for m in members:
            db_user = db.query(User).filter(User.uid == m.uid).first()
            member_list.append({"uid": m.uid, "name": db_user.name})
        count = len(members)
        total = sum(m.price for m in members)
        result.append({
            "orderId": db_team.orderId,
            "ownerId": db_team.ownerId,
            "title": db_team.title,
            "url": db_team.url,
            "location": db_team.location,
            "deliverFee": db_team.deliverFee,
            "endAt": db_team.endAt,
            "description": db_team.description,
            "member": member_list,
            "memberNum": count,
            "totalPrice": total
        })
    return result
@app.post("/api/team/{orderId}/join", response_model=JoinTeamResponse)
def joinTeam(orderId: str, uid: str, jointeam: JoinTeamCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.uid == uid).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    new_join = JoinTeam(orderId=orderId, foodName=jointeam.foodName, price=jointeam.price, uid=uid)
    db.add(new_join)
    db.commit()
    user_name = db_user.name
    return {
        "orderId": new_join.orderId,
        "uid": new_join.uid,
        "name": user_name,
        "foodName": new_join.foodName,
        "status": 0,
        "price": new_join.price
    }
@app.patch("/api/team/{orderId}/join/{uid}", response_model=HandleResponse)
def changeStatus(orderId: str, uid: str, caller_uid: str, jointeam: HandleJoinTeam, db: Session = Depends(get_db)):
    db_team = db.query(Team).filter(Team.orderId == orderId).first()
    if not db_team:
        raise HTTPException(status_code=404, detail="找不到此揪團")

    if caller_uid == db_team.ownerId:
        # 房主：可以接受(1)或婉拒(2)
        if jointeam.status not in [1, 2]:
            raise HTTPException(status_code=403, detail="房主只能接受或婉拒")
    elif caller_uid == uid:
        # 加入者：只能取消(3)
        if jointeam.status != 3:
            raise HTTPException(status_code=403, detail="加入者只能取消申請")
    else:
        raise HTTPException(status_code=403, detail="無權限")

    db_join = db.query(JoinTeam).filter(
        JoinTeam.orderId == orderId,
        JoinTeam.uid == uid
    ).first()
    if not db_join:
        raise HTTPException(status_code=404, detail="找不到此申請")
    else:
        db_join.status = jointeam.status;

    db.commit()
    return {
        "orderId": db_join.orderId,
        "uid": db_join.uid,
        "status": db_join.status
    }
import os

# 靜態檔案目錄（相對於 backend 資料夾的上層 front）
front_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "front")
app.mount("/", StaticFiles(directory=front_dir, html=True), name="front")
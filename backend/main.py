import uuid
from fastapi import FastAPI, Depends, HTTPException, Cookie, Header
import os
import secrets
from datetime import datetime, timedelta, timezone
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

JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_EXPIRE_DAYS", "7"))

def now_utc():
    """統一使用 UTC naive datetime（與 SQLite 儲存格式一致）"""
    return datetime.utcnow()

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = now_utc() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")

def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="access token 已過期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="無效的 access token")
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="access token 缺少使用者資訊")
    return uid

def get_current_uid(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少 Authorization Bearer token")
    return verify_access_token(authorization.split(" ", 1)[1])

@app.post("/api/account/signup", response_model=UserSignupResponse)
def addAccount(user: UserSignupCreate, db: Session = Depends(get_db)):
    uid = str(uuid.uuid4())
    db.add(User(uid=uid, mail=user.mail, name=user.name, hashed_password=user.password))
    db.commit()
    return {"uid": uid}

@app.post("/api/account/login", response_model=UserLoginResponse)
def loginAccount(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.mail == user.mail).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    if user.password != db_user.hashed_password:
        raise HTTPException(status_code=401, detail="帳號密碼錯誤")
    access_token = create_access_token({"sub": db_user.uid, "name": db_user.name})
    refresh_token = secrets.token_urlsafe(32)
    expires_at = now_utc() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(token=refresh_token, uid=db_user.uid, expires_at=expires_at))
    db.commit()
    resp = JSONResponse(content={"access_token": access_token, "token_type": "bearer", "uid": db_user.uid, "name": db_user.name})
    resp.set_cookie("refresh_token", refresh_token, httponly=True, samesite="lax", max_age=REFRESH_TOKEN_EXPIRE_DAYS*24*3600, path="/")
    return resp

@app.post("/api/account/logout")
def logout(refresh_token: str = Cookie(None), db: Session = Depends(get_db)):
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
    if db_token.expires_at and db_token.expires_at < now_utc():
        db.delete(db_token)
        db.commit()
        raise HTTPException(status_code=401, detail="refresh token 已過期")
    db_user = db.query(User).filter(User.uid == db_token.uid).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    return {"access_token": create_access_token({"sub": db_user.uid, "name": db_user.name}), "token_type": "bearer"}

@app.get("/api/account/{uid}", response_model=GetUser)
def getUserData(uid: str, current_uid: str = Depends(get_current_uid), db: Session = Depends(get_db)):
    if current_uid != uid:
        raise HTTPException(status_code=403, detail="無權限存取此使用者資料")
    db_user = db.query(User).filter(User.uid == uid).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    now = now_utc()
    activity_map = {}

    # 自己開的團
    for team in db.query(Team).filter(Team.ownerId == uid).all():
        # endAt 存的是 naive UTC，直接和 now_utc() 比較
        ended = bool(team.endAt and team.endAt < now)
        activity_map[team.orderId] = {
            "type": "gb",
            "title": team.title,
            "date": team.endAt.isoformat() if team.endAt else '',
            "status": "ok" if ended else "pending",
        }

    # 自己申請加入的團
    for join in db.query(JoinTeam).filter(JoinTeam.uid == uid).all():
        if join.orderId in activity_map:
            continue
        team = db.query(Team).filter(Team.orderId == join.orderId).first()
        if not team:
            continue
        ended = bool(team.endAt and team.endAt < now)
        if join.status == 2:
            item_status = "rejected"
        elif ended:
            item_status = "ok"
        else:
            item_status = "pending"
        activity_map[join.orderId] = {
            "type": "gb",
            "title": team.title,
            "date": team.endAt.isoformat() if team.endAt else '',
            "status": item_status,
        }

    history = sorted(activity_map.values(), key=lambda x: x["date"] or '', reverse=True)
    return {"uid": db_user.uid, "name": db_user.name, "mail": db_user.mail, "history": history}

@app.patch("/api/account/{uid}", response_model=GetUser)
def changeUserData(uid: str, user: UserChange, current_uid: str = Depends(get_current_uid), db: Session = Depends(get_db)):
    if current_uid != uid:
        raise HTTPException(status_code=403, detail="無權限修改此使用者資料")
    db_user = db.query(User).filter(User.uid == uid).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    if user.name: db_user.name = user.name
    if user.mail: db_user.mail = user.mail
    if user.password: db_user.hashed_password = user.password
    db.commit()
    return {"uid": db_user.uid, "name": db_user.name, "mail": db_user.mail}

@app.delete("/api/account/{uid}")
def deleteUser(uid: str, password: str, current_uid: str = Depends(get_current_uid), db: Session = Depends(get_db)):
    if current_uid != uid:
        raise HTTPException(status_code=403, detail="無權限刪除此使用者")
    db_user = db.query(User).filter(User.uid == uid).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    if db_user.hashed_password != password:
        raise HTTPException(status_code=401, detail="密碼輸入錯誤")
    db.delete(db_user)
    db.commit()
    return {}

@app.post("/api/team", response_model=TeamResponse)
def createTeam(team: TeamCreate, current_uid: str = Depends(get_current_uid), db: Session = Depends(get_db)):
    orderId = str(uuid.uuid4())
    # 前端送來的 endAt 可能帶時區，統一轉成 naive UTC 再存
    end_at = team.endAt
    if end_at.tzinfo is not None:
        end_at = end_at.astimezone(timezone.utc).replace(tzinfo=None)
    new_team = Team(orderId=orderId, ownerId=current_uid, url=team.url, title=team.title,
                    location=team.location, deliverFee=team.deliverFee,
                    endAt=end_at, description=team.description)
    db.add(new_team)
    db.commit()
    return {
        "orderId": new_team.orderId, "ownerId": new_team.ownerId, "ownerName": None,
        "title": new_team.title, "url": new_team.url, "location": new_team.location,
        "deliverFee": new_team.deliverFee, "endAt": new_team.endAt,
        "description": new_team.description, "member": [], "joinRequests": [],
        "memberNum": 0, "totalPrice": 0
    }

@app.get("/api/team", response_model=List[TeamResponse])
def getTeam(db: Session = Depends(get_db)):
    result = []
    for db_team in db.query(Team).all():
        approved = db.query(JoinTeam).filter(JoinTeam.orderId == db_team.orderId, JoinTeam.status == 1).all()
        pending  = db.query(JoinTeam).filter(JoinTeam.orderId == db_team.orderId, JoinTeam.status == 0).all()
        def to_member(m):
            u = db.query(User).filter(User.uid == m.uid).first()
            return {"uid": m.uid, "name": u.name if u else '匿名', "foodName": m.foodName, "price": m.price, "status": m.status}
        owner = db.query(User).filter(User.uid == db_team.ownerId).first()
        result.append({
            "orderId": db_team.orderId, "ownerId": db_team.ownerId,
            "ownerName": owner.name if owner else '匿名',
            "title": db_team.title, "url": db_team.url, "location": db_team.location,
            "deliverFee": db_team.deliverFee, "endAt": db_team.endAt,
            "description": db_team.description,
            "member": [to_member(m) for m in approved],
            "joinRequests": [to_member(m) for m in pending],
            "memberNum": len(approved), "totalPrice": sum(m.price for m in approved)
        })
    return result

@app.post("/api/team/{orderId}/join", response_model=JoinTeamResponse)
def joinTeam(orderId: str, jointeam: JoinTeamCreate, current_uid: str = Depends(get_current_uid), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.uid == current_uid).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    # 若申請者是團主本人，直接核准（status=1）
    db_team = db.query(Team).filter(Team.orderId == orderId).first()
    is_owner = db_team and db_team.ownerId == current_uid
    init_status = 1 if is_owner else 0
    new_join = JoinTeam(orderId=orderId, foodName=jointeam.foodName, price=jointeam.price,
                        uid=current_uid, status=init_status)
    db.add(new_join)
    db.commit()
    return {"orderId": new_join.orderId, "uid": new_join.uid, "name": db_user.name,
            "foodName": new_join.foodName, "status": init_status, "price": new_join.price}

@app.patch("/api/team/{orderId}/join/{uid}", response_model=HandleResponse)
def changeStatus(orderId: str, uid: str, jointeam: HandleJoinTeam, current_uid: str = Depends(get_current_uid), db: Session = Depends(get_db)):
    db_team = db.query(Team).filter(Team.orderId == orderId).first()
    if not db_team:
        raise HTTPException(status_code=404, detail="找不到此揪團")
    if current_uid == db_team.ownerId:
        if jointeam.status not in [1, 2]:
            raise HTTPException(status_code=403, detail="房主只能接受或婉拒")
    elif current_uid == uid:
        if jointeam.status != 3:
            raise HTTPException(status_code=403, detail="加入者只能取消申請")
    else:
        raise HTTPException(status_code=403, detail="無權限")
    db_join = db.query(JoinTeam).filter(JoinTeam.orderId == orderId, JoinTeam.uid == uid).first()
    if not db_join:
        raise HTTPException(status_code=404, detail="找不到此申請")
    db_join.status = jointeam.status
    db.commit()
    return {"orderId": db_join.orderId, "uid": db_join.uid, "status": db_join.status}

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_teams = db.query(Team).count()
    total_users = db.query(User).count()
    saved_fee = 0
    for team in db.query(Team).all():
        if team.deliverFee:
            count = db.query(JoinTeam).filter(JoinTeam.orderId == team.orderId, JoinTeam.status == 1).count()
            saved_fee += team.deliverFee * count
    return {"active_teams": total_teams, "saved_fee": saved_fee, "total_users": total_users}

front_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "front")
app.mount("/", StaticFiles(directory=front_dir, html=True), name="front")
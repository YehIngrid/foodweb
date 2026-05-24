import uuid
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import (UserSignupCreate, UserSignupResponse, UserLogin, UserLoginResponse
, GetUser, UserChange, DeleteUser, TeamCreate, TeamResponse, JoinTeamCreate
, JoinTeamResponse, HandleJoinTeam, HandleResponse, MemberInfo)
from database import SessionLocal, Base, engine
from models import User, Team, JoinTeam

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
        return {"uid": db_user.uid, "name": db_user.name}

@app.post("/api/account/logout")
def logout():
    return {
    }

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

@app.post("/api/team")
# def createTeam():
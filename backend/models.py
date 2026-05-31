from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "user"

    uid = Column(String, primary_key=True, index=True)
    name = Column(String(20), nullable=False, index=True)
    mail = Column(String(100), unique=True)
    hashed_password = Column(String)

class Team(Base):
    __tablename__ = 'team'

    orderId = Column(String, primary_key=True, index=True)
    title = Column(String(50), index=True)
    url = Column(String(300))
    location = Column(String(30))
    deliverFee = Column(Integer)
    description = Column(String(500), nullable=True)
    endAt = Column(DateTime)
    ownerId = Column(String, ForeignKey("user.uid"))

class JoinTeam(Base):
    __tablename__ = 'joinTeam'

    orderId = Column(String, ForeignKey("team.orderId"), primary_key=True, index=True)
    uid = Column(String, ForeignKey("user.uid"), primary_key=True, index=True)

    foodName = Column(String(20))
    status = Column(Integer, default=0)
    price = Column(Integer)


class RefreshToken(Base):
    __tablename__ = 'refresh_token'

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    uid = Column(String, ForeignKey("user.uid"), nullable=False)
    expires_at = Column(DateTime, nullable=True)

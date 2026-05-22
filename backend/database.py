import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. 💡 載入 .env 檔案的內容
# 這行程式碼會自動在當前目錄尋找 .env 檔案並載入
load_dotenv()

# 2. 💡 讀取環境變數
# 使用 os.getenv("變數名稱") 來取得值
database_url = os.getenv("DATABASE_URL")

# 這裡做個安全檢查，確保有成功讀取到
if not database_url:
    raise ValueError("錯誤：找不到 DATABASE_URL 環境變數，請檢查 .env 檔案！")

engine = create_engine(database_url)

# 3. 💡 建立 SessionLocal 類別
# autocommit=False: 確保每次操作都要明確 commit，交由業務邏輯控制
# autoflush=False: 防止在查詢前自動將未提交的變更同步到資料庫
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 建立 ORM 模型基底
Base = declarative_base()
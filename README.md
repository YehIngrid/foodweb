# 圓食 RoundFood

國立中興大學校園外送揪團平台。讓同學共享外送、分攤運費，一起省更多。

## 專案結構

```
foodweb/
├── backend/          # FastAPI 後端
│   ├── main.py       # 主程式、API 路由
│   ├── models.py     # SQLAlchemy 資料模型
│   ├── schemas.py    # Pydantic 資料驗證
│   ├── database.py   # 資料庫連線設定
│   └── requirements.txt
└── front/
    └── index.html    # 前端單頁應用
```

## 環境需求

- Python 3.10+
- PostgreSQL 資料庫

## 啟動步驟

### 1. 安裝相依套件

> **請務必先執行這步**，否則後端無法啟動。

```bash
cd backend
pip install -r requirements.txt
```

### 2. 設定環境變數

在 `backend/` 目錄下建立 `.env` 檔案：

```env
DATABASE_URL=postgresql://使用者:密碼@localhost:5432/資料庫名稱
JWT_SECRET=你的金鑰
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_EXPIRE_DAYS=7
```

### 3. 啟動後端

```bash
cd backend
uvicorn main:app --reload
```

啟動後前端靜態頁面會一併由後端伺服器提供，開啟瀏覽器前往 [http://localhost:8000](http://localhost:8000) 即可使用。

## API 端點一覽

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/account/signup` | 註冊帳號 |
| POST | `/api/account/login` | 登入 |
| POST | `/api/account/logout` | 登出 |
| POST | `/api/account/refresh` | 刷新 Access Token |
| GET | `/api/account/{uid}` | 查詢會員資料 |
| PATCH | `/api/account/{uid}` | 修改會員資料 |
| DELETE | `/api/account/{uid}` | 刪除帳號 |
| GET | `/api/team` | 取得所有揪團列表 |
| POST | `/api/team` | 建立新揪團 |
| POST | `/api/team/{orderId}/join` | 申請加入揪團 |
| PATCH | `/api/team/{orderId}/join/{uid}` | 審核 / 取消申請 |
| GET | `/api/stats` | 取得平台統計數據 |

## 技術棧

- **後端**：FastAPI、SQLAlchemy ORM、Pydantic、PyJWT
- **資料庫**：PostgreSQL（透過 psycopg2-binary）
- **前端**：純 HTML / CSS / JavaScript（無框架）

## 開發成員

指導教授：黃仲誼 博士  
專案成員：葉潔頤、賴姿妍  
課程：國立中興大學 網際網路系統設計

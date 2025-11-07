from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from database import db, create_document, get_documents, find_one, update_one
from schemas import User, LoginRequest, TokenResponse, TestResponse

SECRET_KEY = "super-secret-fastdevp-key-change"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="FastDevp API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TokenData(BaseModel):
    email: Optional[EmailStr] = None


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.get("/test", response_model=TestResponse)
def test_connection():
    try:
        # quick ping by listing collections
        _ = db.list_collection_names()
        return {"status": "ok", "db": True}
    except Exception:
        return {"status": "ok", "db": False}


@app.post("/auth/register", response_model=TokenResponse)
def register(data: LoginRequest):
    # Only allow registering an admin if none exists yet
    existing_admins = get_documents("user", {"role": "admin"}, limit=1)
    if existing_admins:
        raise HTTPException(status_code=400, detail="Registration disabled: admin already exists")
    user = User(email=data.email, password_hash=get_password_hash(data.password))
    created = create_document("user", user.model_dump())
    token = create_access_token({"sub": created["email"]})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest):
    user = find_one("user", {"email": data.email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}


def get_current_user(token: str) -> dict:
    # Simple token parsing for demonstration (expects raw token from Authorization: Bearer <token>)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = find_one("user", {"email": email})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


@app.get("/admin/overview")
def admin_overview(authorization: Optional[str] = None):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    user = get_current_user(token)
    # return some mock metrics
    return {
        "user": {"email": user["email"], "role": user.get("role", "admin")},
        "metrics": {
            "projects": 24,
            "active_users": 1280,
            "deployments": 57,
        },
    }

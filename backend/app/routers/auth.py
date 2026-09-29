from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ..deps import DbSession
from ..models import User
from ..schemas import LoginRequest, envelope
from ..security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", summary="Xác thực người dùng, trả về JWT")
def login(body: LoginRequest, db: DbSession):
    user = db.scalars(select(User).where(User.username == body.username)).first()

    if user is None or not verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng",
        )

    token = create_access_token(user.user_id, user.username)
    return envelope(
        {
            "token": token,
            "user": {"id": user.user_id, "full_name": user.full_name},
        },
        "Đăng nhập thành công",
    )

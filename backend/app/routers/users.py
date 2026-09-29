from fastapi import APIRouter

from ..deps import CurrentUser
from ..schemas import envelope

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", summary="Thông tin tài khoản người dùng đang đăng nhập")
def get_me(user: CurrentUser):
    return envelope(
        {
            "id": user.user_id,
            "username": user.username,
            "full_name": user.full_name,
            "student_id": user.student_id,
            "class": user.class_name,
        }
    )

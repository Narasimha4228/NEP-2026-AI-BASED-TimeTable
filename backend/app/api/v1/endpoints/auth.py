from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import Response

from app.models.user import User, UserCreate
from app.services.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    create_user_account,
)
from app.core.config import settings

router = APIRouter()


# -----------------------------
# CORS preflight for register
# -----------------------------
@router.options("/register")
async def register_options():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )


# -----------------------------
# LOGIN
# -----------------------------
@router.post("/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login
    """
    user = await authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires,
    )

    # ✅ NO is_admin ANYWHERE
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,            # admin | faculty | student
            "faculty_id": user.faculty_id,
            "group_id": user.group_id,
        },
    }


# -----------------------------
# REGISTER
# -----------------------------
@router.post("/register", response_model=User)
async def register_user(user_data: UserCreate) -> Any:
    """
    Create new user account.
    """
    try:
        user = await create_user_account(user_data)
        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        # Log server-side but do not expose internal exception details to clients
        # (prevents leaking bcrypt/passlib warnings or stack traces)
        import logging
        logging.exception("Unexpected error during registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later.",
        )


# -----------------------------
# TEST TOKEN
# -----------------------------
@router.post("/test-token", response_model=User)
async def test_token(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return current_user


# -----------------------------
# REFRESH TOKEN
# -----------------------------
@router.post("/refresh-token")
async def refresh_token(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    access_token = create_access_token(
        subject=str(current_user.id),
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

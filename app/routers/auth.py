from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.rbac import Role
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    TokenResponse,
)
from app.services.auth_service import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == user_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )

    role_result = await db.execute(select(Role).where(Role.name == "user"))
    default_role = role_result.scalar_one_or_none()
    if not default_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Роль 'user' не найдена. Запустите инициализацию БД.",
        )

    user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        patronymic=user_data.patronymic,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role_id=default_role.id,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        patronymic=user.patronymic,
        email=user.email,
        is_active=user.is_active,
        role_name=default_role.name,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Аккаунт деактивирован",
        )

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"detail": f"Пользователь {current_user.email} вышел из системы"}


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        patronymic=current_user.patronymic,
        email=current_user.email,
        is_active=current_user.is_active,
        role_name=current_user.role.name,
        created_at=current_user.created_at,
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_data = user_data.model_dump(exclude_unset=True)

    if "email" in update_data:
        existing = await db.execute(
            select(User).where(User.email == update_data["email"], User.id != current_user.id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Этот email уже используется другим пользователем",
            )

    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        patronymic=current_user.patronymic,
        email=current_user.email,
        is_active=current_user.is_active,
        role_name=current_user.role.name,
        created_at=current_user.created_at,
    )


@router.delete("/me")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.is_active = False
    await db.commit()
    return {"detail": "Аккаунт деактивирован"}
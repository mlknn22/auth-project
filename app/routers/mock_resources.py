from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.permission_service import check_permission

router = APIRouter(prefix="/api", tags=["Бизнес-ресурсы (mock)"])


MOCK_PRODUCTS = [
    {"id": 1, "name": "Ноутбук ASUS", "price": 79990, "owner_id": 1},
    {"id": 2, "name": "Монитор LG 27''", "price": 24990, "owner_id": 2},
    {"id": 3, "name": "Клавиатура Logitech", "price": 5990, "owner_id": 1},
    {"id": 4, "name": "Мышь Razer", "price": 4490, "owner_id": 3},
]

MOCK_SHOPS = [
    {"id": 1, "name": "TechStore Москва", "city": "Москва", "owner_id": 1},
    {"id": 2, "name": "Digital World", "city": "Санкт-Петербург", "owner_id": 2},
    {"id": 3, "name": "Gadget Hub", "city": "Казань", "owner_id": 3},
]

MOCK_ORDERS = [
    {"id": 1, "product": "Ноутбук ASUS", "quantity": 1, "total": 79990, "owner_id": 1},
    {"id": 2, "product": "Монитор LG 27''", "quantity": 2, "total": 49980, "owner_id": 2},
    {"id": 3, "product": "Мышь Razer", "quantity": 5, "total": 22450, "owner_id": 1},
]


async def check_and_filter(
    db: AsyncSession,
    user: User,
    element_code: str,
    mock_data: list[dict],
) -> list[dict]:
    can_read_all = await check_permission(db, user.role_id, element_code, "read_all")
    if can_read_all:
        return mock_data

    can_read = await check_permission(db, user.role_id, element_code, "read")
    if can_read:
        return [item for item in mock_data if item["owner_id"] == user.id]

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"У вас нет доступа к ресурсу '{element_code}'",
    )


@router.get("/products")
async def get_products(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    products = await check_and_filter(db, current_user, "products", MOCK_PRODUCTS)
    return {"products": products, "total": len(products)}


@router.post("/products")
async def create_product(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    can_create = await check_permission(db, current_user.role_id, "products", "create")
    if not can_create:
        raise HTTPException(status_code=403, detail="Нет прав на создание товаров")
    return {"detail": "Товар создан (mock)", "owner_id": current_user.id}


@router.get("/shops")
async def get_shops(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    shops = await check_and_filter(db, current_user, "shops", MOCK_SHOPS)
    return {"shops": shops, "total": len(shops)}


@router.post("/shops")
async def create_shop(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    can_create = await check_permission(db, current_user.role_id, "shops", "create")
    if not can_create:
        raise HTTPException(status_code=403, detail="Нет прав на создание магазинов")
    return {"detail": "Магазин создан (mock)", "owner_id": current_user.id}


@router.get("/orders")
async def get_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    orders = await check_and_filter(db, current_user, "orders", MOCK_ORDERS)
    return {"orders": orders, "total": len(orders)}


@router.post("/orders")
async def create_order(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    can_create = await check_permission(db, current_user.role_id, "orders", "create")
    if not can_create:
        raise HTTPException(status_code=403, detail="Нет прав на создание заказов")
    return {"detail": "Заказ создан (mock)", "owner_id": current_user.id}
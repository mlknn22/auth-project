from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rbac import Role, BusinessElement, AccessRule
from app.models.user import User
from app.services.auth_service import hash_password


async def init_db(db: AsyncSession):
    existing_role = await db.execute(select(Role).where(Role.name == "admin"))
    if existing_role.scalar_one_or_none():
        return

    roles = [
        Role(name="admin", description="Администратор системы"),
        Role(name="manager", description="Менеджер"),
        Role(name="user", description="Обычный пользователь"),
        Role(name="guest", description="Гость"),
    ]
    db.add_all(roles)
    await db.flush()

    elements = [
        BusinessElement(code="products", name="Товары", description="Управление товарами"),
        BusinessElement(code="shops", name="Магазины", description="Управление магазинами"),
        BusinessElement(code="orders", name="Заказы", description="Управление заказами"),
    ]
    db.add_all(elements)
    await db.flush()

    role_map = {r.name: r.id for r in roles}
    elem_map = {e.code: e.id for e in elements}

    access_rules = [
        AccessRule(
            role_id=role_map["admin"], element_id=elem_map["products"],
            read_permission=True, read_all_permission=True, create_permission=True,
            update_permission=True, update_all_permission=True,
            delete_permission=True, delete_all_permission=True,
        ),
        AccessRule(
            role_id=role_map["admin"], element_id=elem_map["shops"],
            read_permission=True, read_all_permission=True, create_permission=True,
            update_permission=True, update_all_permission=True,
            delete_permission=True, delete_all_permission=True,
        ),
        AccessRule(
            role_id=role_map["admin"], element_id=elem_map["orders"],
            read_permission=True, read_all_permission=True, create_permission=True,
            update_permission=True, update_all_permission=True,
            delete_permission=True, delete_all_permission=True,
        ),
        AccessRule(
            role_id=role_map["manager"], element_id=elem_map["products"],
            read_permission=True, read_all_permission=True, create_permission=True,
            update_permission=True, update_all_permission=False,
            delete_permission=False, delete_all_permission=False,
        ),
        AccessRule(
            role_id=role_map["manager"], element_id=elem_map["shops"],
            read_permission=True, read_all_permission=True, create_permission=False,
            update_permission=False, update_all_permission=False,
            delete_permission=False, delete_all_permission=False,
        ),
        AccessRule(
            role_id=role_map["manager"], element_id=elem_map["orders"],
            read_permission=True, read_all_permission=True, create_permission=True,
            update_permission=True, update_all_permission=False,
            delete_permission=False, delete_all_permission=False,
        ),
        AccessRule(
            role_id=role_map["user"], element_id=elem_map["products"],
            read_permission=True, read_all_permission=True, create_permission=False,
            update_permission=False, update_all_permission=False,
            delete_permission=False, delete_all_permission=False,
        ),
        AccessRule(
            role_id=role_map["user"], element_id=elem_map["shops"],
            read_permission=True, read_all_permission=True, create_permission=False,
            update_permission=False, update_all_permission=False,
            delete_permission=False, delete_all_permission=False,
        ),
        AccessRule(
            role_id=role_map["user"], element_id=elem_map["orders"],
            read_permission=True, read_all_permission=False, create_permission=True,
            update_permission=True, update_all_permission=False,
            delete_permission=False, delete_all_permission=False,
        ),
        AccessRule(
            role_id=role_map["guest"], element_id=elem_map["products"],
            read_permission=True, read_all_permission=True, create_permission=False,
            update_permission=False, update_all_permission=False,
            delete_permission=False, delete_all_permission=False,
        ),
        AccessRule(
            role_id=role_map["guest"], element_id=elem_map["shops"],
            read_permission=True, read_all_permission=True, create_permission=False,
            update_permission=False, update_all_permission=False,
            delete_permission=False, delete_all_permission=False,
        ),
        AccessRule(
            role_id=role_map["guest"], element_id=elem_map["orders"],
            read_permission=False, read_all_permission=False, create_permission=False,
            update_permission=False, update_all_permission=False,
            delete_permission=False, delete_all_permission=False,
        ),
    ]
    db.add_all(access_rules)

    admin_user = User(
        first_name="Admin",
        last_name="Adminov",
        email="admin@example.com",
        hashed_password=hash_password("admin123"),
        role_id=role_map["admin"],
    )
    db.add(admin_user)

    await db.commit()
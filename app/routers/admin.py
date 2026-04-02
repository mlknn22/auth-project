from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_admin_user
from app.models import User
from app.models import Role, BusinessElement, AccessRule
from app.schemas.rbac import (
    RoleCreate,
    RoleResponse,
    BusinessElementCreate,
    BusinessElementResponse,
    AccessRuleCreate,
    AccessRuleUpdate,
    AccessRuleResponse,
)

router = APIRouter(
    prefix="/admin",
    tags=["Администрирование"],
    dependencies=[Depends(get_admin_user)],
)


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role))
    roles = result.scalars().all()
    return [RoleResponse.model_validate(r) for r in roles]


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(role_data: RoleCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Role).where(Role.name == role_data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Роль '{role_data.name}' уже существует",
        )

    role = Role(name=role_data.name, description=role_data.description)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return RoleResponse.model_validate(role)


@router.get("/elements", response_model=list[BusinessElementResponse])
async def list_elements(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BusinessElement))
    elements = result.scalars().all()
    return [BusinessElementResponse.model_validate(e) for e in elements]


@router.post("/elements", response_model=BusinessElementResponse, status_code=status.HTTP_201_CREATED)
async def create_element(element_data: BusinessElementCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(BusinessElement).where(BusinessElement.code == element_data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Элемент с кодом '{element_data.code}' уже существует",
        )

    element = BusinessElement(
        code=element_data.code,
        name=element_data.name,
        description=element_data.description,
    )
    db.add(element)
    await db.commit()
    await db.refresh(element)
    return BusinessElementResponse.model_validate(element)


@router.get("/access-rules", response_model=list[AccessRuleResponse])
async def list_access_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AccessRule))
    rules = result.scalars().all()
    return [
        AccessRuleResponse(
            id=rule.id,
            role_id=rule.role_id,
            role_name=rule.role.name,
            element_id=rule.element_id,
            element_code=rule.element.code,
            read_permission=rule.read_permission,
            read_all_permission=rule.read_all_permission,
            create_permission=rule.create_permission,
            update_permission=rule.update_permission,
            update_all_permission=rule.update_all_permission,
            delete_permission=rule.delete_permission,
            delete_all_permission=rule.delete_all_permission,
        )
        for rule in rules
    ]


@router.post("/access-rules", response_model=AccessRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_access_rule(rule_data: AccessRuleCreate, db: AsyncSession = Depends(get_db)):
    role = await db.get(Role, rule_data.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")

    element = await db.get(BusinessElement, rule_data.element_id)
    if not element:
        raise HTTPException(status_code=404, detail="Бизнес-элемент не найден")

    existing = await db.execute(
        select(AccessRule).where(
            AccessRule.role_id == rule_data.role_id,
            AccessRule.element_id == rule_data.element_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Правило для этой пары роль-элемент уже существует",
        )

    rule = AccessRule(**rule_data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return AccessRuleResponse(
        id=rule.id,
        role_id=rule.role_id,
        role_name=role.name,
        element_id=rule.element_id,
        element_code=element.code,
        read_permission=rule.read_permission,
        read_all_permission=rule.read_all_permission,
        create_permission=rule.create_permission,
        update_permission=rule.update_permission,
        update_all_permission=rule.update_all_permission,
        delete_permission=rule.delete_permission,
        delete_all_permission=rule.delete_all_permission,
    )


@router.put("/access-rules/{rule_id}", response_model=AccessRuleResponse)
async def update_access_rule(
    rule_id: int,
    rule_data: AccessRuleUpdate,
    db: AsyncSession = Depends(get_db),
):
    rule = await db.get(AccessRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Правило не найдено")

    update_data = rule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)

    return AccessRuleResponse(
        id=rule.id,
        role_id=rule.role_id,
        role_name=rule.role.name,
        element_id=rule.element_id,
        element_code=rule.element.code,
        read_permission=rule.read_permission,
        read_all_permission=rule.read_all_permission,
        create_permission=rule.create_permission,
        update_permission=rule.update_permission,
        update_all_permission=rule.update_all_permission,
        delete_permission=rule.delete_permission,
        delete_all_permission=rule.delete_all_permission,
    )


@router.delete("/access-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_access_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    rule = await db.get(AccessRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Правило не найдено")

    await db.delete(rule)
    await db.commit()


@router.put("/users/{user_id}/role")
async def assign_role(user_id: int, role_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")

    user.role_id = role_id
    await db.commit()

    return {"detail": f"Пользователю {user.email} назначена роль '{role.name}'"}
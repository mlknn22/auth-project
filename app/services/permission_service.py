from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rbac import AccessRule, BusinessElement


async def check_permission(
    db: AsyncSession,
    role_id: int,
    element_code: str,
    permission_type: str,
) -> bool:
    query = (
        select(AccessRule)
        .join(BusinessElement)
        .where(
            AccessRule.role_id == role_id,
            BusinessElement.code == element_code,
        )
    )

    result = await db.execute(query)
    rule = result.scalar_one_or_none()

    if rule is None:
        return False

    permission_map = {
        "read": rule.read_permission,
        "read_all": rule.read_all_permission,
        "create": rule.create_permission,
        "update": rule.update_permission,
        "update_all": rule.update_all_permission,
        "delete": rule.delete_permission,
        "delete_all": rule.delete_all_permission,
    }

    return permission_map.get(permission_type, False)
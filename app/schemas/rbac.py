from pydantic import BaseModel


class RoleCreate(BaseModel):
    name: str
    description: str | None = None


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class BusinessElementCreate(BaseModel):
    code: str
    name: str
    description: str | None = None


class BusinessElementResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class AccessRuleCreate(BaseModel):
    role_id: int
    element_id: int
    read_permission: bool = False
    read_all_permission: bool = False
    create_permission: bool = False
    update_permission: bool = False
    update_all_permission: bool = False
    delete_permission: bool = False
    delete_all_permission: bool = False


class AccessRuleUpdate(BaseModel):
    read_permission: bool | None = None
    read_all_permission: bool | None = None
    create_permission: bool | None = None
    update_permission: bool | None = None
    update_all_permission: bool | None = None
    delete_permission: bool | None = None
    delete_all_permission: bool | None = None


class AccessRuleResponse(BaseModel):
    id: int
    role_id: int
    role_name: str
    element_id: int
    element_code: str
    read_permission: bool
    read_all_permission: bool
    create_permission: bool
    update_permission: bool
    update_all_permission: bool
    delete_permission: bool
    delete_all_permission: bool

    model_config = {"from_attributes": True}
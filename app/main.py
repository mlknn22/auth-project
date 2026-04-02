from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine, async_session, Base
from app.models import User, Role, BusinessElement, AccessRule
from app.routers import auth, admin, mock_resources
from app.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        await init_db(session)

    yield

    await engine.dispose()


app = FastAPI(
    title="Auth System API",
    description="Система аутентификации и авторизации",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(mock_resources.router)


@app.get("/")
async def root():
    return {"message": "Auth System API работает. Перейдите на /docs для документации."}
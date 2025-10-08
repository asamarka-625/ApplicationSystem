# Внешние зависимости
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
# Внутренние модули
from web_app.src.core import config, setup_database, engine
from web_app.src.routers import router
from web_app.src.admin import UserAdmin, ItemAdmin, CategoryAdmin


async def startup():
    config.logger.info("Инициализируем базу данных...")
    await setup_database()


async def shutdown():
    config.logger.info("Останавливаем приложение...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup логика
    await startup()
    yield
    # Shutdown логика
    await shutdown()


app = FastAPI(lifespan=lifespan)

# Подключение маршрутов
app.include_router(router)

# app.mount("/static", StaticFiles(directory="web_app/src/static"), name="static")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

admin = Admin(app, engine)
admin.add_view(UserAdmin)
admin.add_view(ItemAdmin)
admin.add_view(CategoryAdmin)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', port=8000, reload=False)
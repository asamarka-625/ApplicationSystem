"""""""""""""""""""""""""""Внешние зависимости"""""""""""""""""""""""""""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
"""""""""""""""""""""""""""Внутренние модули"""""""""""""""""""""""""""
from web_app.src.routers import main_router
from web_app.src.utils import redis_cache_rank, redis_cache_doubler, redis_cache_daily_task, redis_cache_tap, redis_pubsub_manager, redis_cache_news
from web_app.src.work.doubler_worker import start_game_worker
from data_base.database import setup_database

app = FastAPI()

# Подключение маршрутов
app.include_router(main_router)

app.mount("/static", StaticFiles(directory="web_app/src/static"), name="static")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    

@app.on_event("startup")
async def startup_event():
    await setup_database()
    print('База данных инициализирована')
    
    await redis_cache_rank.init()
    await redis_cache_tap.init()
    await redis_cache_doubler.init()
    await redis_pubsub_manager.init()
    await redis_cache_daily_task.init()
    await redis_cache_news.init()
    await redis_cache_news.init_news()
    print('Redis подключен')
    
    asyncio.create_task(start_game_worker())
    

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении приложения"""
    await redis_cache_rank.close()
    await redis_cache_tap.close()
    await redis_cache_doubler.close()
    await redis_pubsub_manager.close()
    await redis_cache_daily_task.close()
    await redis_cache_news.close()
    print("Redis отключен")

        
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', port=8000, reload=False)
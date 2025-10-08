"""""""""""""""""""""""""""Внешние зависимости"""""""""""""""""""""""""""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from typing import List, Dict, Optional
import asyncio
import json
from datetime import datetime
import uuid
"""""""""""""""""""""""""""Внутренние модули"""""""""""""""""""""""""""
from web_app.src.schemas.doubler_schem import BetRequestModel
from web_app.src.dependencies.dependencies_for_cookie import get_current_user, get_token_from_websocket
from web_app.src.crud.crud_users import sql_update_balance_coins_user
from data_base.models import Users
from web_app.config import get_config
from web_app.src.utils import redis_cache_doubler, redis_pubsub_manager


router = APIRouter()
config = get_config()


@router.websocket("/doubler/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Depends(get_token_from_websocket)):
    user = await get_current_user(token)

    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    websocket_id = f"{id(websocket)}_{user.id}"
    
    try:
        await websocket.accept()
        
        # Добавляем соединение в Redis
        await redis_pubsub_manager.add_connection(websocket_id, user.id, websocket)
        await redis_cache_doubler.update_user_balance_cache(user.id, user.coins)
        
        # Отправляем текущее состояние игры
        game_state = await redis_cache_doubler.get_game_state()
        if game_state and game_state.get("current_round"):
            await websocket.send_json({
                "type": "round_update",
                "round": game_state["current_round"],
                "history": game_state.get("history", [])[-10:],
                "balance": user.coins
            })
        
        try:
            # Просто ждем пока соединение не разорвется
            await websocket.receive()
        except WebSocketDisconnect:
            print(f"WebSocket disconnected for user {user.id}")
            
        except Exception as e:
            print(f"WebSocket error: {e}")
            
    except Exception as err:
        print(f'WebSocket error: {err}')
        
    finally:
        # Удаляем соединение из менеджера
        await redis_pubsub_manager.remove_connection(websocket_id, user.id)
        try:
            await websocket.close()
        except:
            pass


async def wait_for_disconnect(websocket: WebSocket):
    try:
        while True:
            if websocket not in active_connections:
                break
                
            await asyncio.sleep(1)
            
    except:
        pass


@router.post("/doubler/place_bet")
async def place_bet(bet: BetRequestModel, user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    # Блокировка на уровне пользователя
    lock_key = f"user_bet_lock:{user.id}"
    lock = redis_cache_doubler.redis.lock(lock_key, timeout=3, blocking_timeout=2)
    
    try:
        # Пытаемся получить блокировку
        if not await lock.acquire():
            raise HTTPException(status_code=429, detail="Please wait, processing previous bet")
            
        # Получаем текущее состояние игры
        game_state = await redis_cache_doubler.get_game_state()
        current_round = game_state.get("current_round", {})
        
        if not current_round or current_round.get("status") != "waiting" or bet.round_id != current_round.get("id"):
            raise HTTPException(status_code=400, detail="Betting is closed for current round")
        
        if user.telegram_id > 0:
            # Атомарная проверка баланса
            can_bet = await redis_cache_doubler.atomic_balance_check(user.id, bet.amount)
            if not can_bet:
                raise HTTPException(status_code=400, detail="Not enough balance")
            
        # Проверяем баланс и списываем средства
        success, new_balance = await sql_update_balance_coins_user(user.id, bet.amount * (-1))
        if not success:
            # Откатываем Redis баланс
            await redis_cache_doubler.redis.incrby(f"user_balance:{user.id}", bet.amount)
            raise HTTPException(status_code=400, detail="Not enough balance")
    
        # Сохраняем ставку в Redis
        bet_data = {
            "amount": bet.amount,
            "bet_type": bet.bet_type,
            "name": user.name,
            "avatar": user.person.image if user.person else None,
            "flame": user.flame.name if user.flame else None,
            "outline": config.AVATAR_OUTLINE_COLORS.get(user.outline.name),
            "level": user.level,
            "vip": bool(user.vip),
            "timestamp": datetime.now().isoformat()
        }
    
        await redis_cache_doubler.add_bet(bet.round_id, user.id, bet_data)        
        await redis_pubsub_manager.publish_user_balance_update(
            user.id,
            message={
                "balance": new_balance,
                "win": False
            }
        )
        
        return {
            "message": "Bet placed successfully", 
            "new_balance": new_balance,
            "round_id": bet.round_id
        }
        
    finally:
        try:
            await lock.release()
        except:
            pass


@router.get("/doubler/game_state")
async def get_game_state(user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    game_state = await redis_cache_doubler.get_game_state()
    current_round = game_state.get("current_round", {})
    
    return {
        "current_round": current_round,
        "history": game_state.get("history", [])[-10:],
        "balance": await redis_cache_doubler.get_user_balance_cache(user.id) or user.coins
    }


@router.get("/doubler/current_round_id")
async def get_current_round(user: Optional[Users] = Depends(get_current_user)):
    if user is None or user.telegram_id >= 0:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    game_state = await redis_cache_doubler.get_game_state()
    current_round = game_state.get("current_round", {})
    
    if current_round and current_round.get("status") == "waiting":
        round_id = current_round["id"]
    else:
        round_id = None
    
    return {
        "status": "success",
        "round_id": round_id
    }
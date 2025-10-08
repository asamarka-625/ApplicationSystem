"""""""""""""""""""""""""""Внешние зависимости"""""""""""""""""""""""""""
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
import httpx
import json
from typing import Optional, List
from datetime import datetime, timedelta, time
"""""""""""""""""""""""""""Внутренние модули"""""""""""""""""""""""""""
from web_app.src.crud.crud_settings import (sql_get_settings_economy, sql_update_settings_economy, sql_add_game_level, sql_update_game_level,
                                            sql_delete_game_level, sql_add_news, sql_update_news, sql_add_promo_code)
from web_app.src.crud.crud_users import (sql_exchange_diamonds_user, sql_transfer_tickets, sql_test_daily, sql_test_give_flame, sql_test_give_avatar_outline,
                                         sql_get_rewards_for_level_user, sql_achievements_claim_user, sql_test_give_item_in_market, sql_get_inventory_user,
                                         sql_get_items_from_market, sql_buy_item_user_from_market, sql_sell_items_from_inventory_user, sql_equip_item_for_user, sql_test_add_item,
                                         sql_get_prize_draws, sql_add_prize_draws, sql_update_prize_draws, sql_participate_prize_draws, sql_add_special,
                                         sql_add_daily_task, sql_activate_promo_for_user, sql_create_purchase_item_from_market, sql_create_purchase_item_from_donate)
from web_app.src.schemas.steam_schem import SteamIdRequestModel, SteamIdResponseModel, SteamInventoryResponseModel
from web_app.src.schemas.settings_schem import SettingsEconomyModel
from web_app.src.schemas.main_schem import (ExchangeDiamondsModel, TransferTicketsModel, LevelRequestModel, ItemRequestModel, ItemSellRequestModel, ParticipateModel,
                                            DailyTaskModel, SubscriptionResponseModel, PromoCodeModel, DonateRequestModel)
from web_app.src.work.logic_steam import get_steamid64, is_valid_steamid64, format_inventory_response
from web_app.src.dependencies.dependencies_for_cookie import get_current_user
from web_app.src.work.daily_reward_service import DailyRewardService
from data_base.models import Users
from web_app.config import get_config
from web_app.src.utils import redis_cache_rank, redis_cache_daily_task, redis_cache_news


router = APIRouter()
config = get_config()


"""""""""""""""""""""""""""API STEAM"""""""""""""""""""""""""""

# Получение steamId64 и ссылку на avatar профиля стим
@router.post("/api/v1/resolve-steamid", response_model=SteamIdResponseModel)
async def resolve_steamid(request: SteamIdRequestModel, user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    steam_input = request.steamId.strip()
    
    steamId64 = await get_steamid64(steam_input)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://api/v1.steampowered.com/ISteamUser/GetPlayerSummaries/v2/',
                params={'key': config.STEAM_API_KEY, 'steamids': steamId64},
                timeout=10
            )
        
            response.raise_for_status()
            data = response.json()
            
            if not data:
                raise HTTPException(
                    status_code=404,
                    detail="Профиль не найден или профиль скрыт"
                )
            
            result = SteamIdResponseModel(steamId64=steamId64, avatar=data['response']['players'][0]['avatar'])
            
            return result
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Таймаут при запросе к Steam")
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка при запросе инвентаря: {str(e)}"
        )
    
    # Если ничего не сработало
    raise HTTPException(
        status_code=400,
        detail="Неверный формат SteamID. Поддерживаются: SteamID64, STEAM_X:Y:Z, Trade URL или Vanity URL"
    )


# Получение инвентаря
@router.get("/api/v1/steam-inventory", response_model=List[Optional[SteamInventoryResponseModel]])
async def get_inventory(steamId64: str = Query(...), app_id: int = Query(730), context_id: int = Query(2), user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    if not is_valid_steamid64(steamId64):
        raise HTTPException(status_code=400, detail="Неверный SteamID64")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://steamcommunity.com/inventory/{steamId64}/{app_id}/{context_id}",
                params={"l": "russian", "count": 200, "key": config.STEAM_API_KEY},
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get("success", False):
                raise HTTPException(
                    status_code=404,
                    detail="Инвентарь не найден или профиль скрыт"
                )
                
            return await format_inventory_response(data['assets'], data['descriptions'])
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Таймаут при запросе к Steam")
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка при запросе инвентаря: {str(e)}"
        )
        
       
"""""""""""""""""""""""""""API APP"""""""""""""""""""""""""""

# Обмен diamonds в tickets
@router.post("/api/v1/exchange-diamonds", response_class=JSONResponse)
async def exchange_diamonds(data: ExchangeDiamondsModel, user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    result = await sql_exchange_diamonds_user(user.id, data.amount)
    
    if result is None:
        raise HTTPException(status_code=400, detail="Unable to complete exchange")
        
    return {"status": "success", **result} 
    

# Перевод tickets другому user
@router.post("/api/v1/transfer-tickets", response_class=JSONResponse)
async def transfer_tickets(data: TransferTicketsModel, user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    tickets = await sql_transfer_tickets(user.id, data.recipientId, data.amount)
    
    if tickets is None:
        raise HTTPException(status_code=400, detail="Unable to complete transfer")
        
    return {"status": "success", "newTickets": tickets}


# Получение leaderboard
@router.get("/api/v1/leaderboard", response_class=JSONResponse)
async def get_leaderboard(rank_type: str, user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    if rank_type not in ["coins", "friends_invited", "sponsor_value"]:
        raise HTTPException(400, detail="Invalid rank type")
    
    if cached := await redis_cache_rank.get_data(f"top:{rank_type}"):
        players = []
        for c in cached:
            c['outline'] = config.AVATAR_OUTLINE_COLORS[c['outline']]
            players.append(c)
        
        if rank_type == 'sponsor_value' and user.sponsor_value == 0:
            current_rank = '-'
            
        else:
            current_rank = await redis_cache_rank.get_user_rank(user.id, rank_type)
            
        return {
            "status": "success",
            "players": players,
            "currentUser": {
                "current_rank": current_rank,
                "name": user.name,
                "avatar": user.person.image,
                "level": user.level,
                "value": getattr(user, rank_type),
                "outline": config.AVATAR_OUTLINE_COLORS[user.outline.name],
                "flame": user.flame.name if user.flame else None,
                "vip": bool(user.vip)
            }
        }
    

"""""""""""""""""""""""""""Работа с daily"""""""""""""""""""""""""""

# Получение ежедневной награды
@router.post("/api/v1/daily/claim", response_class=JSONResponse)
async def daily_claim(user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    daily_reward = DailyRewardService(user.id, user.last_claimed_mega_drop, user.last_claimed_daily, user.last_reward_day, user.current_streak)
    
    try:
        result = await daily_reward.claim_daily_reward()
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Error claim")
    
    else:
        return result
        

# Получение мега-дропа
@router.post("/api/v1/daily/mega-drop", response_class=JSONResponse)
async def mega_drop_claim(user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    daily_reward = DailyRewardService(user.id, user.last_claimed_mega_drop, user.last_claimed_daily, user.last_reward_day, user.current_streak)
    
    try:
        result = await daily_reward.claim_mega_drop()
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Error claim")
    
    else:
        return result


# Получение наград за уровни
@router.get("/api/v1/achievements/rewards", response_class=JSONResponse)
async def get_achievements_rewards(user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    result = await sql_get_rewards_for_level_user(user.id)
        
    return {"status": "success", "rewards": result, "user": {"level": user.level, "exp": user.experience}}


# Забираем награду за уровень
@router.post("/api/v1/achievements/claim", response_class=JSONResponse)
async def achievements_claim(data: LevelRequestModel, user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    if data.level > user.level or data.level not in config.LEVELS_REWARDS:
        raise HTTPException(status_code=400, detail="There is no required level")
        
    try:
        result = await sql_achievements_claim_user(user.id, data.level)
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Error claim")
    
    else:
        return {"status": "success", **result}
                    

"""""""""""""""""""""""""""Работа с инвентарем"""""""""""""""""""""""""""

# Получение инвентаря
@router.get("/api/v1/inventory", response_class=JSONResponse)
async def get_inventory(
    user: Optional[Users] = Depends(get_current_user)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    result = await sql_get_inventory_user(user)
    
    return {"status": "success", "result": result, "inventory_limit": user.inventory_limit}
    

# Продажа предметов из инвентаря
@router.post("/api/v1/sell-items")
async def sell_items(
    data: ItemSellRequestModel,
    user: Optional[Users] = Depends(get_current_user)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    try:
        diamonds = await sql_sell_items_from_inventory_user(user.id, data.items)
    
    except Exception as err:
        print(err)
        raise HTTPException(status_code=400, detail="Failed to sell item")
    
    else:
        return {"status": "success", "diamonds": diamonds}
    

# Экипировка предмета из инвентаря  
@router.post("/api/v1/equip-item")
async def equip_item(
    item: ItemRequestModel,
    user: Optional[Users] = Depends(get_current_user)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    try:
        result = await sql_equip_item_for_user(user.id, item.item_id)
    
    except Exception as err:
        print(err)
        raise HTTPException(status_code=400, detail="Failed to equip item")
        
    else:
        return {"status": "success", "result": result}
        

"""""""""""""""""""""""""""Работа с маркетом"""""""""""""""""""""""""""

# Получение маркета
@router.get("/api/v1/market", response_class=JSONResponse)
async def get_market(
    type: str,
    user: Optional[Users] = Depends(get_current_user)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    if type not in ["skins", "persons", "visuals", "specials"]:
        raise HTTPException(400, detail="Invalid type")
        
    result = await sql_get_items_from_market(type)
    
    return {"status": "success", "result": result}
   

# Покупка предмета с маркета
@router.post("/api/v1/buy", response_class=JSONResponse)
async def buy_item_from_market(
    data: ItemRequestModel,
    user: Optional[Users] = Depends(get_current_user)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    try:
        new_tickets = await sql_buy_item_user_from_market(user.id, data.item_id)
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Error buy item")
        
    return {"status": "success", "new_tickets": new_tickets}
    

"""""""""""""""""""""""""""Работа с розыгрышами"""""""""""""""""""""""""""

# Получение розыгрышей
@router.get("/api/v1/giveaways", response_class=JSONResponse)
async def get_giveaways(user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    result = await sql_get_prize_draws(user.id)
    
    return {"status": "success", "giveaways": result}    
    

# Принять участие в розыгрыше
@router.post("/api/v1/giveaways/participate", response_class=JSONResponse)
async def participate_giveaways(data: ParticipateModel, user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    try:
        await sql_participate_prize_draws(user.id, data.giveaway_id)
    
    except:
        raise HTTPException(status_code=400, detail="Error accepting participation")
        
    return {"status": "success"} 
    

"""""""""""""""""""""""""""Ежедневные задания"""""""""""""""""""""""""""

# Получение ежедневных задач пользователя
@router.get("/api/v1/daily_tasks", response_class=JSONResponse)
async def get_daily_tasks(user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    tasks = await redis_cache_daily_task.get_user_tasks(user.id)
    
    if not tasks:
        await redis_cache_daily_task.create_tasks(user_id=user.id, user_level=user.level, weapon_level=user.weapon.required_level)
        tasks = await redis_cache_daily_task.get_user_tasks(user.id)
    
    now = datetime.now()
    end_of_day = datetime.combine(now.date() + timedelta(days=1), time.min)
        
    return {
        "status": "success",
        "tasks": tasks,
        "completed_tasks": sum(1 for task in tasks if task["completed"]),
        "end_time": int((end_of_day - now).total_seconds())
    }


# Получить награду за задание
@router.post("/api/v1/daily_tasks/reward", response_class=JSONResponse)
async def get_reward_for_daily_tasks(data: DailyTaskModel, user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    try:
        tickets = await redis_cache_daily_task.claimed_reward_completed(user_id=user.id, task_id=data.task_id)
    
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
        
    else:
        return {"status": "success", "tickets": tickets}
    

# Обновить задание - просмотр рекламы
@router.post("/api/v1/daily_tasks/ads_view", response_class=JSONResponse)
async def update_ads_view_daily_tasks(data: DailyTaskModel, user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    try:
        await redis_cache_daily_task.update_definite_task_progress(user_id=user.id, task_id=data.task_id, task_type='ads_view', increment=1)
    
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
        
    else:
        return {"status": "success"}
        

async def check_telegram_subscription(user_id: int, channel: str) -> dict:
    """
    Проверяет подписку пользователя через Telegram Bot API
    """
    url = f"https://api.telegram.org/bot{config.SUBSCRIPTION_BOT_TOKEN}/getChatMember"
    
    params = {
        "chat_id": channel,
        "user_id": user_id
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Telegram API error: {str(e)}")
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Telegram API unavailable")


def is_user_subscribed(telegram_response: dict) -> bool:
    """
    Проверяет статус подписки из ответа Telegram API
    """
    if not telegram_response.get("ok"):
        return False
    
    result = telegram_response.get("result", {})
    status = result.get("status", "")
    
    # Пользователь подписан если имеет один из этих статусов
    valid_statuses = ["creator", "administrator", "member", "restricted"]
    return status in valid_statuses


@router.post("/api/v1/daily_tasks/check-subscription", response_model=SubscriptionResponseModel)
async def check_subscription(data: DailyTaskModel, user: Optional[Users] = Depends(get_current_user)):
    """
    Проверяет подписку пользователя на канал
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    try:
        channel = await redis_cache_daily_task.get_channel_task(user_id=user.id, task_id=data.task_id)
        
        # Проверяем подписку через Telegram API
        telegram_response = await check_telegram_subscription(user.telegram_id, channel)
        
        subscribed = is_user_subscribed(telegram_response)
        
        if subscribed:
            await redis_cache_daily_task.update_definite_task_progress(user_id=user.id, task_id=data.task_id, task_type='subscribe_channel', increment=1)
            
        return SubscriptionResponseModel(
            subscribed=subscribed,
            status=telegram_response.get("result", {}).get("status")
        )
        
    except HTTPException as e:
        return SubscriptionResponseModel(
            subscribed=False,
            error='Error check subscription'
        )
    except Exception as e:
        return SubscriptionResponseModel(
            subscribed=False,
            error='Error check subscription'
        )


"""""""""""""""""""""""""""Промокод"""""""""""""""""""""""""""

# Активация промокода
@router.post("/api/v1/activate_promo", response_class=JSONResponse)
async def activate_promo(data: PromoCodeModel, user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    result = await sql_activate_promo_for_user(user.id, data.code)
    
    return result

    
"""""""""""""""""""""""""""Настройки"""""""""""""""""""""""""""

# Получение экономическийх настроек
@router.get("/api/v1/settings/economy", response_model=SettingsEconomyModel)
async def get_settings_economy():
    result = await sql_get_settings_economy()
    
    return result

        
"""""""""""""""""""""""""""Новости"""""""""""""""""""""""""""

# Получение последних новостей
@router.get("/api/v1/news", response_class=JSONResponse)
async def get_latest_news():
    news = await redis_cache_news.get_news()
        
    return news
    

"""""""""""""""""""""""""""Оплата звездами"""""""""""""""""""""""""""

@router.post("/api/v1/payments/create-invoice")
async def create_invoice(data: ItemRequestModel, user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    try:
        info = await sql_create_purchase_item_from_market(user.id, data.item_id)
       
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    
    except Exception as err:
        print(f"Unexpected error in create_invoice: {err}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
    # Формируем данные для инвойса
    invoice_data = {
        "title": info["name"],
        "description": "Предмет из маркета",
        "payload": str(info["purchase_id"]),
        "provider_token": "",
        "currency": "XTR",
        "prices": [{"label": info["name"], "amount": info["price"]}]
    }
        
    invoice_url = await create_telegram_invoice(invoice_data)
    
    return {"invoice_url": invoice_url}
    

@router.post("/api/v1/payments/donate/create-invoice")
async def create_donate_invoice(data: DonateRequestModel, user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    try:
        purchase_id = await sql_create_purchase_item_from_donate(user.id, data.amount)
    
    except Exception as err:
        print(f"Unexpected error in create_invoice: {err}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
    # Формируем данные для инвойса
    invoice_data = {
        "title": "Поддержка проекта",
        "description": "💖 Ваш донат пойдет на развитие проекта",
        "payload": str(purchase_id),
        "provider_token": "",
        "currency": "XTR",
        "prices": [{"label": "Donate", "amount": data.amount}]
    }
        
    invoice_url = await create_telegram_invoice(invoice_data)
    
    return {"invoice_url": invoice_url}
    
    
async def create_telegram_invoice(invoice_data: dict) -> str:
    """
    Создает инвойс через Telegram Bot API и возвращает URL
    """
    try:
        # URL для создания инвойса через Bot API
        bot_api_url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/createInvoiceLink"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(bot_api_url, json=invoice_data)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                raise HTTPException(
                    status_code=400,
                    detail="Telegram API error"
                )
           
            return data['result']
                    
    except Exception as e:
        print(f"Error creating Telegram invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to create invoice")
        
        
""" TEST """

# Добавляем новый промокод
@router.get("/api/v1/add/promocode", response_class=JSONResponse)
async def add_prom_ocode(
    code: str,
    tickets: int,
    max_uses: int,
    days_from: int = 0,
    days_until: int = 15
):
    try:
        await sql_add_promo_code(code=code, tickets=tickets, max_uses=max_uses, days_from=days_from, days_until=days_until)
        
    except:
        raise HTTPException(status_code=400, detail="Error")
        
    return {"status": "success"}
    
    
# Добавляем новую новость
@router.get("/api/v1/add/news", response_class=JSONResponse)
async def add_news(
    title: str,
    content: str,
    subtitle: Optional[str] = None,
    image: Optional[str] = None,
    features: Optional[str] = None
):
    features_list = features.split(",") if features else None
    
    await sql_add_news(title=title, content=content, subtitle=subtitle, image=image, features=features_list)
    await redis_cache_news.init_news()
    
    return {"status": "success"}
    

# Обновляем новость
@router.get("/api/v1/update/news", response_class=JSONResponse)
async def update_news(
    id_news: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    subtitle: Optional[str] = None,
    image: Optional[str] = None,
    features: Optional[str] = None
):
    features_list = features.split(",") if features else None
    
    await sql_update_news(id_news=id_news, title=title, content=content, subtitle=subtitle, image=image, features=features_list)
    await redis_cache_news.init_news()
    
    return {"status": "success"}
    
    
# Добавляем новое задание
@router.get("/api/v1/add/daily_task", response_class=JSONResponse)
async def add_daily_task(type: str, reward: int, description: str, channel_id: Optional[str] = None, min_target: Optional[int] = None, max_target: Optional[int] = None):
    await sql_add_daily_task(type=type, reward=reward, description=description, channel_id=channel_id, min_target=min_target, max_target=max_target)
    
    return {"status": "success"}
    
    
# Добавляем новый уровень
@router.get("/api/v1/add/game_level", response_class=JSONResponse)
async def add_game_level(name: str, image: str, type_drop: str, time: int, cost: int, currency: str, type: str):
    await sql_add_game_level(name=name, image=image, type_drop=type_drop, time=time, cost=cost, currency=currency, type=type)
    
    return {"status": "success"}
    

# Обновляем уровень
@router.get("/api/v1/update/game_level", response_class=JSONResponse)
async def update_game_level(
    level_id: int,
    name: Optional[str] = None, 
    image: Optional[str] = None, 
    type_drop: Optional[str] = None, 
    time: Optional[int] = None, 
    cost: Optional[int] = None, 
    currency: Optional[str] = None, 
    type: Optional[str] = None
):
    await sql_update_game_level(level_id=level_id, name=name, image=image, type_drop=type_drop, time=time, cost=cost, currency=currency, type=type)
    
    return {"status": "success"}


# Обновляем уровень
@router.get("/api/v1/delete/game_level", response_class=JSONResponse)
async def delete_game_level(level_id: int):
    result = await sql_delete_game_level(level_id=level_id)
    
    return {"status": "success", "result": 'delete success' if result else 'level not found'}
    
    
# Добавляем розыгрыш
@router.get("/api/v1/add/giveaways", response_class=JSONResponse)
async def add_giveaways(
    item_id: int,
    tickets: int,
    price: float,
    hours: int = 3
):
    result = await sql_add_prize_draws(item_id=item_id, tickets=tickets, price=price, hours=hours)
    
    return {"status": "success"}
    
 
# Обновляем розыгрыш
@router.get("/api/v1/update/giveaways", response_class=JSONResponse)
async def update_giveaways(
    prize_id: int,
    item_id: Optional[int] = None,
    tickets: Optional[int] = None,
    price: Optional[float] = None,
    hours: Optional[int] = None,
    minutes: int = 0
):
    await sql_update_prize_draws(prize_id, item_id=item_id, tickets=tickets, price=price, hours=hours, minutes=minutes)
    
    return {"status": "success"}

       
# Добавляем предмет в маркет
@router.get("/api/v1/add/item/market", response_class=JSONResponse)
async def add_item_in_market(item_id: int, type: str, currency: str, price: int):
    await sql_test_give_item_in_market(item_id, type, currency, price)
    
    return {"status": "success"}
    
    
# Обновление экономическийх настроек
@router.get("/api/v1/update/settings/economy", response_class=JSONResponse)
async def update_settings_economy(rate: float, fee: float, referral: int):
    await sql_update_settings_economy(rate, fee, referral)
    
    return {"status": "success"}
    

# Делаем -1 день
@router.get("/api/v1/daily/test", response_class=JSONResponse)
async def test_daily(user_id: int, add_days: int):
    await sql_test_daily(user_id, add_days)
    
    return {"status": "success"}
    

# Обновляем flame    
@router.get("/api/v1/effects/flame", response_class=JSONResponse)
async def test_give_flame(user_id: int, value: Optional[str] = None):
    await sql_test_give_flame(user_id, value)
    
    return {"status": "success"}


# Обновляем avatar_outline
@router.get("/api/v1/effects/avatar-outline", response_class=JSONResponse)
async def test_give_avatar_outline(user_id: int, value: Optional[str] = None):
    await sql_test_give_avatar_outline(user_id, value)
    
    return {"status": "success"}
    

@router.get("/api/v1/get_item")
async def get_item(
    user_id: int,
    item_id: int,
    quantity: int = 1
):
    await sql_get_item_for_user(user_id, skin_id)
    
    return {"status": "success"}


@router.get("/api/v1/add/person")
async def add_person(
    name: str,
    image: str,
    price: float,
    chance: float
):
    await sql_add_person(name, image, price, chance)
    
    return {"status": "success"}
    

@router.get("/api/v1/add/flame")
async def add_flame(
    name: str,
    price: float
):
    await sql_add_flame(name, price)
    
    return {"status": "success"}
    

@router.get("/api/v1/add/outline")
async def add_outline(
    name: str,
    price: float
):
    await sql_add_outline(name, price)
    
    return {"status": "success"}


@router.get("/api/v1/add/special")
async def add_special(
    name: str,
    descrip: str,
    image: Optional[str] = None,
    price: Optional[float] = None
):
    await sql_add_special(name, image, descrip, price)
    
    return {"status": "success"}
    
    
@router.get("/api/v1/add/inventory")
async def add_item_in_inventory(
    user_id: int,
    item_id: int,
):
    try:
        await sql_test_add_item(user_id, item_id)
        
    except ValueError as err:
        return {"error": str(err)}
        
    return {"status": "success"}

    
@router.get("/api/v1/equip/item")
async def equip_item(
    user_id: int,
    item_id: int,
):
    pass
    # await sql_equip_item_for_user(user_id, None, item_id)
    
    # return {"status": "success"}
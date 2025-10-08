"""""""""""""""""""""""""""Внешние зависимости"""""""""""""""""""""""""""
from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import Response, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime
"""""""""""""""""""""""""""Внутренние модули"""""""""""""""""""""""""""
from web_app.src.schemas.telegram_schem import InfoUserModel
from web_app.src.work.valid_user import check_webapp_signature
from web_app.src.dependencies.dependencies_for_cookie import create_access_token, get_current_user
from web_app.src.work.daily_reward_service import DailyRewardService
from data_base.models import Users
from web_app.config import get_config
from web_app.src.utils import redis_cache_daily_task, redis_cache_news
from web_app.src.crud.crud_users import sql_update_last_login_user, sql_update_check_news_user


router = APIRouter()
config = get_config()
templates = Jinja2Templates(directory="web_app/templates")


def get_daily_user_data(user: Users):
    daily_reward = DailyRewardService(user.id, user.last_claimed_mega_drop, user.last_claimed_daily, user.last_reward_day, user.current_streak)
    return daily_reward.get_rewards_from_user(user.daily_rewards)
        

"""""""""""""""""""""""""""Проверка"""""""""""""""""""""""""""

@router.post('/userIsValid', response_class=JSONResponse)
async def check_hash(request: InfoUserModel, response: Response):
    if request.hash and request.checkDataString:
        user = await check_webapp_signature(request)

        if user:
            access_token = await create_access_token({"sub": str(user.telegram_id)})
            
            response.set_cookie(key=f"users_access_token", value=access_token, httponly=True, samesite="None", secure=True)
            
            return {'status': 'success'}
            
    raise HTTPException(status_code=401, detail="Not authorized")
    

"""""""""""""""""""""""""""HTML PAGES"""""""""""""""""""""""""""

# Home
@router.get("/home", response_class=HTMLResponse)
async def home_page(request: Request, background_tasks: BackgroundTasks, user: Optional[Users] = Depends(get_current_user)):
    context = {
        'request': request,
    }
    
    if user is not None:
        background_tasks.add_task(sql_update_last_login_user, user.id)
        
        if user.last_login:
            is_update, date_news = await redis_cache_news.check_view_news_for_user(user.check_news)
            if is_update:
                background_tasks.add_task(sql_update_check_news_user, user.id, date_news)
                
            context['news'] = is_update
            
        else:
            context['news'] = False
           
        await redis_cache_daily_task.create_tasks(user_id=user.id, user_level=user.level, weapon_level=user.weapon.required_level)
        
        now = datetime.now()
        daily = await get_daily_user_data(user)
        context.update(daily)
        
        context['title'] = 'Home'
        context['page'] = 'home'
        context['name'] = user.name
        context['level'] = user.level
        context['tickets'] = user.coins
        context['diamonds'] = f'{user.diamonds:.5f}'
        context['avatar'] = user.person.image
        context['avatar_outline'] = config.AVATAR_OUTLINE_COLORS[user.outline.name]
        context['flame'] = user.flame.name if user.flame else None
        context['notifications'] = user.notifications
        context['tutorial'] = user.last_login is None
        context['vip_expiration_timestamp'] = (user.vip - now).total_seconds() if user.vip else 0
        context['damage_expiration_timestamp'] = (user.double_damage - now).total_seconds() if user.double_damage else 0
        context['exp_expiration_timestamp'] = (user.double_exp - now).total_seconds() if user.double_exp else 0
        context['luck_expiration_timestamp'] = (user.bonus_luck - now).total_seconds() if user.bonus_luck else 0
        context['vip'] = context['vip_expiration_timestamp'] > 0
        context['special_timer'] = (context['vip_expiration_timestamp'] > 0 or context['damage_expiration_timestamp'] > 0 
                                    or context['exp_expiration_timestamp'] > 0 or context['luck_expiration_timestamp'] > 0)
        
        return templates.TemplateResponse('home.html', context=context)
        
    else:
        return templates.TemplateResponse(name=f"login_telegram.html", context=context)
        
        
# Inventory
@router.get("/inventory", response_class=HTMLResponse)
async def inventory_page(request: Request, background_tasks: BackgroundTasks, user: Optional[Users] = Depends(get_current_user)):
    context = {
        'request': request,
    }
    
    if user is not None:
        background_tasks.add_task(sql_update_last_login_user, user.id)
        
        if user.last_login:
            is_update, date_news = await redis_cache_news.check_view_news_for_user(user.check_news)
            if is_update:
                background_tasks.add_task(sql_update_check_news_user, user.id, date_news)
                
            context['news'] = is_update
            
        else:
            context['news'] = False
        
        await redis_cache_daily_task.create_tasks(user_id=user.id, user_level=user.level, weapon_level=user.weapon.required_level)
        
        now = datetime.now()
        daily = await get_daily_user_data(user)
        context.update(daily)
        
        context['title'] = 'Inventory | Продажа скинов'
        context['page'] = 'inventory'
        context['name'] = user.name
        context['level'] = user.level
        context['tickets'] = user.coins
        context['diamonds'] = f'{user.diamonds:.5f}'
        context['avatar'] = user.person.image
        context['avatar_outline'] = config.AVATAR_OUTLINE_COLORS[user.outline.name]
        context['flame'] = user.flame.name if user.flame else None
        context['notifications'] = user.notifications
        context['tutorial'] = user.last_login is None
        context['vip_expiration_timestamp'] = (user.vip - now).total_seconds() if user.vip else 0
        context['damage_expiration_timestamp'] = (user.double_damage - now).total_seconds() if user.double_damage else 0
        context['exp_expiration_timestamp'] = (user.double_exp - now).total_seconds() if user.double_exp else 0
        context['luck_expiration_timestamp'] = (user.bonus_luck - now).total_seconds() if user.bonus_luck else 0
        context['vip'] = context['vip_expiration_timestamp'] > 0
        context['special_timer'] = (context['vip_expiration_timestamp'] > 0 or context['damage_expiration_timestamp'] > 0 
                                    or context['exp_expiration_timestamp'] > 0 or context['luck_expiration_timestamp'] > 0)
        
        return templates.TemplateResponse('inventory.html', context=context)
        
    else:
        return templates.TemplateResponse(name=f"login_telegram.html", context=context)
    
  
# Games
@router.get("/games", response_class=HTMLResponse)
async def games_page(request: Request, background_tasks: BackgroundTasks, user: Optional[Users] = Depends(get_current_user)):    
    context = {
        'request': request,
    }
    
    if user is not None:
        background_tasks.add_task(sql_update_last_login_user, user.id)
        
        if user.last_login:
            is_update, date_news = await redis_cache_news.check_view_news_for_user(user.check_news)
            if is_update:
                background_tasks.add_task(sql_update_check_news_user, user.id, date_news)
                
            context['news'] = is_update
            
        else:
            context['news'] = False
        
        await redis_cache_daily_task.create_tasks(user_id=user.id, user_level=user.level, weapon_level=user.weapon.required_level)
        
        now = datetime.now()
        daily = await get_daily_user_data(user)
        context.update(daily)
        
        context['title'] = 'Games'
        context['page'] = 'games'
        context['name'] = user.name
        context['level'] = user.level
        context['tickets'] = user.coins
        context['diamonds'] = f'{user.diamonds:.5f}'
        context['avatar'] = user.person.image
        context['avatar_outline'] = config.AVATAR_OUTLINE_COLORS[user.outline.name]
        context['flame'] = user.flame.name if user.flame else None
        context['notifications'] = user.notifications
        context['tutorial'] = user.last_login is None
        context['vip_expiration_timestamp'] = (user.vip - now).total_seconds() if user.vip else 0
        context['damage_expiration_timestamp'] = (user.double_damage - now).total_seconds() if user.double_damage else 0
        context['exp_expiration_timestamp'] = (user.double_exp - now).total_seconds() if user.double_exp else 0
        context['luck_expiration_timestamp'] = (user.bonus_luck - now).total_seconds() if user.bonus_luck else 0
        context['vip'] = context['vip_expiration_timestamp'] > 0
        context['special_timer'] = (context['vip_expiration_timestamp'] > 0 or context['damage_expiration_timestamp'] > 0 
                                    or context['exp_expiration_timestamp'] > 0 or context['luck_expiration_timestamp'] > 0)
        
        return templates.TemplateResponse('games.html', context=context)
        
    else:
        return templates.TemplateResponse(name=f"login_telegram.html", context=context)

        
# Doubler game
@router.get("/doubler", response_class=HTMLResponse)
async def doubler_page(request: Request, background_tasks: BackgroundTasks, user: Optional[Users] = Depends(get_current_user)):
    context = {
        'request': request,
    }
    
    if user is not None:
        background_tasks.add_task(sql_update_last_login_user, user.id)
        
        if user.last_login:
            is_update, date_news = await redis_cache_news.check_view_news_for_user(user.check_news)
            if is_update:
                background_tasks.add_task(sql_update_check_news_user, user.id, date_news)
                
            context['news'] = is_update
            
        else:
            context['news'] = False
        
        await redis_cache_daily_task.create_tasks(user_id=user.id, user_level=user.level, weapon_level=user.weapon.required_level)
        
        now = datetime.now()
        daily = await get_daily_user_data(user)
        context.update(daily)
        
        context['title'] = 'Doubler'
        context['page'] = 'doubler'
        context['name'] = user.name
        context['level'] = user.level
        context['tickets'] = user.coins
        context['diamonds'] = f'{user.diamonds:.5f}'
        context['avatar'] = user.person.image
        context['avatar_outline'] = config.AVATAR_OUTLINE_COLORS[user.outline.name]
        context['flame'] = user.flame.name if user.flame else None
        context['notifications'] = user.notifications
        context['tutorial'] = user.last_login is None
        context['vip_expiration_timestamp'] = (user.vip - now).total_seconds() if user.vip else 0
        context['damage_expiration_timestamp'] = (user.double_damage - now).total_seconds() if user.double_damage else 0
        context['exp_expiration_timestamp'] = (user.double_exp - now).total_seconds() if user.double_exp else 0
        context['luck_expiration_timestamp'] = (user.bonus_luck - now).total_seconds() if user.bonus_luck else 0
        context['vip'] = context['vip_expiration_timestamp'] > 0
        context['special_timer'] = (context['vip_expiration_timestamp'] > 0 or context['damage_expiration_timestamp'] > 0 
                                    or context['exp_expiration_timestamp'] > 0 or context['luck_expiration_timestamp'] > 0)
        
        return templates.TemplateResponse('doubler.html', context=context)
        
    else:
        return templates.TemplateResponse(name=f"login_telegram.html", context=context)
    
    
# Tap
@router.get("/tap", response_class=HTMLResponse)
async def tap_page(request: Request, background_tasks: BackgroundTasks, user: Optional[Users] = Depends(get_current_user)):
    context = {
        'request': request,
    }
    
    if user is not None:
        background_tasks.add_task(sql_update_last_login_user, user.id)
        
        if user.last_login:
            is_update, date_news = await redis_cache_news.check_view_news_for_user(user.check_news)
            if is_update:
                background_tasks.add_task(sql_update_check_news_user, user.id, date_news)
                
            context['news'] = is_update
            
        else:
            context['news'] = False
            
        await redis_cache_daily_task.create_tasks(user_id=user.id, user_level=user.level, weapon_level=user.weapon.required_level)
        
        now = datetime.now()
        daily = await get_daily_user_data(user)
        context.update(daily)
            
        context['title'] = 'BUBBLE TAP'
        context['page'] = 'tap'
        context['name'] = user.name
        context['level'] = user.level
        context['tickets'] = user.coins
        context['diamonds'] = f'{user.diamonds:.5f}'
        context['avatar'] = user.person.image
        context['avatar_outline'] = config.AVATAR_OUTLINE_COLORS[user.outline.name]
        context['flame'] = user.flame.name if user.flame else None
        context['notifications'] = user.notifications
        context['tutorial'] = user.last_login is None
        context['vip_expiration_timestamp'] = (user.vip - now).total_seconds() if user.vip else 0
        context['damage_expiration_timestamp'] = (user.double_damage - now).total_seconds() if user.double_damage else 0
        context['exp_expiration_timestamp'] = (user.double_exp - now).total_seconds() if user.double_exp else 0
        context['luck_expiration_timestamp'] = (user.bonus_luck - now).total_seconds() if user.bonus_luck else 0
        context['vip'] = context['vip_expiration_timestamp'] > 0
        context['special_timer'] = (context['vip_expiration_timestamp'] > 0 or context['damage_expiration_timestamp'] > 0 
                                    or context['exp_expiration_timestamp'] > 0 or context['luck_expiration_timestamp'] > 0)
        
        return templates.TemplateResponse('tapalka.html', context=context)
        
    else:
        return templates.TemplateResponse(name=f"login_telegram.html", context=context)

    
# Profile
@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, background_tasks: BackgroundTasks, user: Optional[Users] = Depends(get_current_user)):
    context = {
        'request': request,
    }
    
    if user is not None:
        background_tasks.add_task(sql_update_last_login_user, user.id)
        
        if user.last_login:
            is_update, date_news = await redis_cache_news.check_view_news_for_user(user.check_news)
            if is_update:
                background_tasks.add_task(sql_update_check_news_user, user.id, date_news)
                
            context['news'] = is_update
            
        else:
            context['news'] = False
        
        await redis_cache_daily_task.create_tasks(user_id=user.id, user_level=user.level, weapon_level=user.weapon.required_level)
        tasks = await redis_cache_daily_task.get_user_tasks(user.id)
        completed_tasks = sum(1 for task in tasks if task["completed"])
        
        now = datetime.now()
        daily = await get_daily_user_data(user)
        context.update(daily)
        
        context['title'] = 'PROFILE'
        context['page'] = 'profile'
        context['name'] = user.name
        context['user_id'] = user.telegram_id
        context['level'] = user.level
        context['tickets'] = user.coins
        context['diamonds'] = f'{user.diamonds:.5f}'
        context['avatar'] = user.person.image
        context['daily_streak'] = user.current_streak
        context['avatar_outline'] = config.AVATAR_OUTLINE_COLORS[user.outline.name]
        context['flame'] = user.flame.name if user.flame else None
        context['friends_invited'] = user.friends_invited
        context['referral_tickets_earned'] = user.referral_tickets_earned
        context['notifications'] = user.notifications
        context['tutorial'] = user.last_login is None
        context['referral_link'] = user.referral_link
        context['check_channel'] = user.check_channel
        context['telegram_channel'] = config.TELEGRAM_CHANNEL
        context['achievements'] = config.LEN_REWARDS_FOR_LEVELS
        context['achievements_completed'] = config.get_completed_levels(user.level)
        context['vip_expiration_timestamp'] = (user.vip - now).total_seconds() if user.vip else 0
        context['damage_expiration_timestamp'] = (user.double_damage - now).total_seconds() if user.double_damage else 0
        context['exp_expiration_timestamp'] = (user.double_exp - now).total_seconds() if user.double_exp else 0
        context['luck_expiration_timestamp'] = (user.bonus_luck - now).total_seconds() if user.bonus_luck else 0
        context['vip'] = context['vip_expiration_timestamp'] > 0
        context['special_timer'] = (context['vip_expiration_timestamp'] > 0 or context['damage_expiration_timestamp'] > 0 
                                    or context['exp_expiration_timestamp'] > 0 or context['luck_expiration_timestamp'] > 0)
        context['completed_tasks'] = completed_tasks
        context['count_tasks'] = len(tasks)
        
        return templates.TemplateResponse('profile.html', context=context)
        
    else:
        return templates.TemplateResponse(name=f"login_telegram.html", context=context)
        
"""""""""""""""""""""""""""Внешние зависимости"""""""""""""""""""""""""""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import time
import uuid
import asyncio
import math
from typing import List, Optional
from datetime import datetime, timedelta
"""""""""""""""""""""""""""Внутренние модули"""""""""""""""""""""""""""
from web_app.src.schemas.main_schem import (GameStateModel, GameStateUpdateModel, CharacterModel, WeaponModel, LevelsModel, PlayerStateModel,
                                            CurrentWeaponStateModel, RoundStateModel, SessionStateModel, BoostStatModel)
from web_app.src.crud.crud_items import sql_get_random_cases_with_skins
from web_app.src.crud.crud_users import (sql_update_data_users, sql_update_energy_user, sql_update_last_used_dps_user, sql_credit_diamonds_dps_user,
                                         sql_update_tickets_user, sql_give_boosts_user)
from web_app.src.crud.crud_settings import sql_get_game_levels
from web_app.src.dependencies.dependencies_for_cookie import get_current_user
from data_base.models import Users
from web_app.config import get_config
from web_app.src.utils import redis_cache_tap, redis_cache_daily_task


router = APIRouter()
security = HTTPBearer()
config = get_config()


# Генерируем кейсы с дропам в них
async def generate_characters(user: Users, type: str, count_case: int) -> List[CharacterModel]:
    cases_skins = await sql_get_random_cases_with_skins(
        type=type,
        count_case=count_case,
        user_luck=50 if user.bonus_luck is not None else user.person.luck
    )
    result = []

    enemy_health = config.calculate_enemy_health_adjustment(user.level, user.weapon.required_level)
    enemy_lifetime = config.ENEMY_LIFETIME
    enemy_exp = config.calculate_enemy_exp(user.level) * (2 if user.double_exp is not None and user.double_exp > datetime.now() else 1)

    for case_skin in cases_skins:
        case, skin = case_skin['case'], case_skin['skin']
        
        weapon = WeaponModel(
            name_weapon=skin.name_weapon if hasattr(skin, 'name_weapon') else '',
            name=skin.name,
            souvenir=skin.souvenir,
            quality=skin.quality if hasattr(skin, 'quality') else '',
            image=skin.image,
            bg=config.BG_RARITY[skin.rarity]
        )
        
        character = CharacterModel(
            item_id=skin.id,
            required_level=skin.required_level,
            price=skin.price,
            charid=str(uuid.uuid4()),
            name=case.name,
            image=case.image,
            bg='bg-green-900',
            initialHealth=enemy_health,
            characterLifetime=enemy_lifetime,
            exp_for_kill=enemy_exp,
            weapon=weapon,
        )
        
        result.append(character)
        
    return result
    

# Инициализируем новую сессию
@router.post("/tap/init", response_class=JSONResponse)
async def init_session(user: Optional[Users] = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    session_token = str(uuid.uuid4())
    
    weapon = user.weapon
    
    time_left = None
    if user.time_for_max_energy is not None:
        time_passed = (datetime.now() - user.time_for_max_energy).total_seconds()
        
        if time_passed < 0:
            time_left = abs(time_passed)
    
    bonus_luck = user.bonus_luck is not None and user.bonus_luck > datetime.now()
    double_damage = user.double_damage is not None and user.double_damage > datetime.now()
        
    game_state = GameStateModel(
        player=PlayerStateModel(
            diamonds=user.diamonds,
            max_score=user.max_score,
            luck=50 if bonus_luck else user.person.luck,
            level=user.level,
            level_up_threshold=user.level_up_threshold,
            experience=user.experience,
            max_available_level=config.RANGE_DAMAGE_FOR_PLAYER + weapon.required_level,
            energy_limit=user.energy_limit,
            energy_rate=user.energy_rate,
            current_energy=user.current_energy,
            inventory_occupancy=user.inventory_occupancy,
            inventory_limit=user.inventory_limit,
            add_damage=weapon.damage if double_damage else 0,
            full_damage=weapon.damage * (2 if double_damage else 1),
            volume_diamonds_dps=config.calculate_volume_diamonds(user.level),
            _last_used_diamonds_dps=user.last_used_diamonds_dps,
            _speed_diamonds_dps=weapon.dps,
            _last_energy_update=user.time_for_max_energy or datetime.now()
        ),
        current_weapon=CurrentWeaponStateModel(
            name=weapon.name,
            dps=weapon.dps,
            damage=weapon.damage,
            crit=weapon.crit
        ),
    )
    
    types_level = ('base', 'premium') if user.vip is not None else ('base', )
    game_levels, game_levels_full = await sql_get_game_levels(types=types_level)
    
    session_state = SessionStateModel(
        game_state=game_state,
        game_levels=game_levels_full,
        last_action=time.time()
    )
    
    lock_key = f"user_tap_lock:{user.id}"
    lock = redis_cache_tap.redis.lock(lock_key, timeout=5, blocking_timeout=2)
    
    try:
        # Пытаемся получить блокировку
        if not await lock.acquire():
            raise HTTPException(status_code=429, detail="Please wait, processing previous request")
            
        if user.last_used_diamonds_dps is None:
            session_state.game_state.player._last_used_diamonds_dps = datetime.now()
            await sql_update_last_used_dps_user(user.id, game_state.player)
            
        if time_left is None and user.current_energy < user.energy_limit:
            session_state.game_state.player._stored_energy = user.energy_limit
            session_state.game_state.player._last_energy_update = datetime.now()
            await sql_update_energy_user(user.id, game_state.player)
    
        await redis_cache_tap.set_data(f"session:{session_token}", session_state.model_dump(), ttl=1800)
        
        return {
            "status": "success",
            "session_token": session_token,
            **game_state.model_dump(),
            "current_energy": game_state.player.current_energy,
            "time_left_energy": game_state.player.time_left_energy,
            "diamonds_dps": game_state.player.diamonds_dps,
            "base_xp": config.BASE_EXP,
            "growth_factor": config.GROWTH_FACTOR_LEVEL,
            "game_levels": game_levels
        }
    
    finally:
        try:
            await lock.release()
        except:
            pass
            
    raise HTTPException(status_code=400, detail="Error init")
                

# Инициализируем уровень          
@router.post("/tap/start-level", response_class=JSONResponse)
async def start_level(
    level: LevelsModel,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user: Optional[Users] = Depends(get_current_user)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    token = credentials.credentials
    
    session_data = await redis_cache_tap.get_data(f"session:{token}")
    if not session_data:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    session_data['game_state']['player'].update({
        'current_energy':user.current_energy,
        '_last_used_diamonds_dps': user.last_used_diamonds_dps,
        '_speed_diamonds_dps': user.weapon.dps,
        '_last_energy_update': user.time_for_max_energy or datetime.now()
    })
    session_state = SessionStateModel(**session_data)
    
    # Защита от DDoS: ограничение частоты запросов
    current_time = time.time()
    if (current_time - session_state.last_action) < 0.1:  # 100ms
        raise HTTPException(status_code=429, detail="Too many requests")
    
    round_data = await redis_cache_tap.get_data(f"round_game:{token}")
    if round_data:
        raise HTTPException(status_code=400, detail="The game has already been initialized")
    
    if level.name not in session_state.game_levels or (user.vip is None and session_state.game_levels[level.name]['type'] == 'premium'):
        raise HTTPException(status_code=422, detail="There is no level")
        
    lock_key = f"user_tap_lock:{user.id}"
    lock = redis_cache_tap.redis.lock(lock_key, timeout=5, blocking_timeout=2)
    
    try:
        # Пытаемся получить блокировку
        if not await lock.acquire():
            raise HTTPException(status_code=429, detail="Please wait, processing previous request")
            
        current_tickets = user.coins
        
        if session_state.game_levels[level.name]['currency'] == 'energy' and not session_state.game_state.player.consume_energy(session_state.game_levels[level.name]['cost']):
            raise HTTPException(status_code=400, detail="Not enough energy")
        
        elif session_state.game_levels[level.name]['currency'] == 'tickets' and current_tickets < session_state.game_levels[level.name]['cost']:
            raise HTTPException(status_code=400, detail="Not enough tickets")
    
        characters = await generate_characters(
            user=user,
            type=session_state.game_levels[level.name]['type_drop'],
            count_case=math.ceil(session_state.game_levels[level.name]['time'] / (config.SPAWN_INTERVAL / 1000))
        )
        round_state = RoundStateModel(
            tap=0,
            score=0,
            combo=0,
            exp=0,
            diamonds=0,
            killed_characters={},
            characters={character.charid: character for character in characters}
        )
 
        session_state.last_action = current_time
        
        if session_state.game_levels[level.name]['currency'] == 'energy':
            await sql_update_energy_user(user.id, session_state.game_state.player)
            
        elif session_state.game_levels[level.name]['currency'] == 'tickets':
            current_tickets = current_tickets - session_state.game_levels[level.name]['cost']
            await sql_update_tickets_user(user.id, current_tickets)
            
        await redis_cache_tap.set_data(f"round_game:{token}", round_state.model_dump(), ttl=(session_state.game_levels[level.name]['time'] + 5))
        await redis_cache_tap.update_session_keep_ttl(f"session:{token}", session_state.model_dump())
        
        return {
            "status": "success",
            "current_energy": session_state.game_state.player.current_energy,
            "current_tickets": current_tickets,
            "time_left_energy": session_state.game_state.player.time_left_energy,
            "characters": [character.model_dump(exclude={"item_id", "required_level", "price"}) for character in characters],
            "spawn_interval": config.SPAWN_INTERVAL
        }
        
    finally:
        try:
            await lock.release()
        except:
            pass
            
    raise HTTPException(status_code=400, detail="Error start-level")
    

# Закрываем уровень
@router.post("/tap/end-level", response_class=JSONResponse)
async def end_level(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user: Optional[Users] = Depends(get_current_user)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    token = credentials.credentials
    
    session_data = await redis_cache_tap.get_data(f"session:{token}")
    if not session_data:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    session_data['game_state']['player'].update({
        'current_energy':user.current_energy,
        '_last_used_diamonds_dps': user.last_used_diamonds_dps,
        '_speed_diamonds_dps': user.weapon.dps,
        '_last_energy_update': user.time_for_max_energy or datetime.now()
    })
    session_state = SessionStateModel(**session_data)
    
    # Защита от DDoS: ограничение частоты запросов
    current_time = time.time()
    if (current_time - session_state.last_action) < 0.1:
        raise HTTPException(status_code=429, detail="Too many requests")
    
    round_data = await redis_cache_tap.get_data(f"round_game:{token}")
    if not round_data:
        raise HTTPException(status_code=400, detail="No run game")
        
    lock_key = f"user_tap_lock:{user.id}"
    lock = redis_cache_tap.redis.lock(lock_key, timeout=5, blocking_timeout=2)
    
    try:
        # Пытаемся получить блокировку
        if not await lock.acquire():
            raise HTTPException(status_code=429, detail="Please wait, processing previous request")
            
        round_state = RoundStateModel(**round_data)
        session_state.last_action = current_time
        
        if round_state.score > session_state.game_state.player.max_score:
            session_state.game_state.player.max_score = round_state.score
        
        bonus_luck = user.bonus_luck is not None and user.bonus_luck > datetime.now()
        double_damage = user.double_damage is not None and user.double_damage > datetime.now()
        
        session_state.game_state.player.luck = 50 if bonus_luck else user.person.luck
        session_state.game_state.player.add_damage = user.weapon.damage if double_damage else 0
        session_state.game_state.player.full_damage = user.weapon.damage * (2 if double_damage else 1)
        session_state.game_state.player.energy_limit = user.energy_limit
        session_state.game_state.player.energy_rate = user.energy_rate
        session_state.game_state.player.inventory_limit = user.inventory_limit
        
        session_state.game_state.player.diamonds = await sql_update_data_users(
            user_id=user.id,
            player_state=session_state.game_state.player,
            killed_characters=round_state.killed_characters
        )
        
        await redis_cache_tap.delete_data(f"round_game:{token}")
        await redis_cache_tap.update_session_keep_ttl(f"session:{token}", session_state.model_dump())
        await redis_cache_daily_task.update_task_progress(user.id, round_state.model_dump())
        
        return {
            "status": "success",
            **session_state.game_state.model_dump(),
            "score": round_state.score,
            "combo": round_state.combo,
            "earned_diamonds": round_state.diamonds,
            "earned_items": sum(1 for item in round_state.killed_characters.values() if not item)
        }
    
    finally:
        try:
            await lock.release()
        except:
            pass
        
    raise HTTPException(status_code=400, detail="Error end-level")
    

# Обновляем удар по кейсу
@router.post("/tap/update", response_class=JSONResponse)
async def update_state(
    game_update: GameStateUpdateModel,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user: Optional[Users] = Depends(get_current_user)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    token = credentials.credentials
    
    session_data = await redis_cache_tap.get_data(f"session:{token}")
    if not session_data:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    session_data['game_state']['player'].update({
        'current_energy':user.current_energy,
        '_last_used_diamonds_dps': user.last_used_diamonds_dps,
        '_speed_diamonds_dps': user.weapon.dps,
        '_last_energy_update': user.time_for_max_energy or datetime.now()
    })
    session_state = SessionStateModel(**session_data)
    
    # Защита от DDoS: ограничение частоты запросов
    current_time = time.time()
    if (current_time - session_state.last_action) < 0.1:
        raise HTTPException(status_code=429, detail="Too many requests")
    
    round_data = await redis_cache_tap.get_data(f"round_game:{token}")
    if not round_data:
        raise HTTPException(status_code=400, detail="No run game")
    
    # Атомарное обновление состояния
    lock_key = f"user_session_lock:{token}"
    lock = redis_cache_tap.redis.lock(lock_key, timeout=2, blocking_timeout=1)
    
    try:
        # Пытаемся получить блокировку
        if not await lock.acquire():
            raise HTTPException(status_code=429, detail="Please wait, processing previous request")
            
        round_state = RoundStateModel(**round_data)
        session_state.last_action = current_time
        
        for update in game_update.updates:
            
            if update.charid not in round_state.characters:
                continue
            
            round_state.tap += 1
            damage = int(round(1 + round_state.combo * 0.1, 1) * session_state.game_state.player.full_damage * (session_state.game_state.current_weapon.crit if round_state.tap % 11 == 0 else 1))
            round_state.characters[update.charid].initialHealth -= damage
            round_state.score += damage
           
            if round_state.characters[update.charid].initialHealth <= 0:
                session_state.game_state.player.experience = min(
                    session_state.game_state.player.experience + round_state.characters[update.charid].exp_for_kill, session_state.game_state.player.level_up_threshold
                )
                round_state.combo += 1
                round_state.exp += round_state.characters[update.charid].exp_for_kill
                
                sell_item = (game_update.autoSell and user.level > round_state.characters[update.charid].required_level) or session_state.game_state.player.inventory_occupancy >= session_state.game_state.player.inventory_limit
                round_state.killed_characters[round_state.characters[update.charid].item_id] = sell_item
                if sell_item:
                    round_state.diamonds += round_state.characters[update.charid].price
                    
                else:
                    session_state.game_state.player.inventory_occupancy += 1
                
                del round_state.characters[update.charid]
                
                if session_state.game_state.player.experience >= session_state.game_state.player.level_up_threshold and user.level < session_state.game_state.player.max_available_level:
                    session_state.game_state.player.experience = 0
                    session_state.game_state.player.level += 1
                    session_state.game_state.player.level_up_threshold = config.xp_for_level(session_state.game_state.player.level)
        
        await redis_cache_tap.update_session_keep_ttl(f"round_game:{token}", round_state.model_dump())
        await redis_cache_tap.update_session_keep_ttl(f"session:{token}", session_state.model_dump())
            
        return {"status": "success", "inventory_occupancy": session_state.game_state.player.inventory_occupancy}
    
    finally:
        try:
            await lock.release()
        except:
            pass
            
    raise HTTPException(status_code=400, detail="Error update")
    

# Добавляем буст
@router.post("/tap/boost", response_class=JSONResponse)
async def boost_stat(
    data: BoostStatModel,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user: Optional[Users] = Depends(get_current_user)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    token = credentials.credentials
    
    session_data = await redis_cache_tap.get_data(f"session:{token}")
    if not session_data:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    session_data['game_state']['player'].update({
        'current_energy':user.current_energy,
        '_last_used_diamonds_dps': user.last_used_diamonds_dps,
        '_speed_diamonds_dps': user.weapon.dps,
        '_last_energy_update': user.time_for_max_energy or datetime.now()
    })
    session_state = SessionStateModel(**session_data)
    
    # Защита от DDoS: ограничение частоты запросов
    current_time = time.time()
    if (current_time - session_state.last_action) < 0.1:
        raise HTTPException(status_code=429, detail="Too many requests")
    
    # Атомарное обновление состояния
    lock_key = f"user_tap_lock:{user.id}"
    lock = redis_cache_tap.redis.lock(lock_key, timeout=3, blocking_timeout=2)
    
    try:
        # Пытаемся получить блокировку
        if not await lock.acquire():
            raise HTTPException(status_code=429, detail="Please wait, processing previous request")
            
        session_state.last_action = current_time
        data_attr = {
            'data-vip-end': user.vip,
            'data-exp-end': user.double_exp,
            'data-damage-end': user.double_damage,
            'data-luck-end': user.bonus_luck
        }
        
        if data.boost == 'damage':
            session_state.game_state.player.add_damage = user.weapon.damage
            session_state.game_state.player.full_damage = user.weapon.damage * 2
            data_attr['data-damage-end'] = await sql_give_boosts_user(boost='double_damage', boost_minutes=1, user_id=user.id)
            
        elif data.boost == 'luck':
            session_state.game_state.player.luck = 50
            data_attr['data-luck-end'] = await sql_give_boosts_user(boost='bonus_luck', boost_minutes=1, user_id=user.id)
        
        else:
            raise HTTPException(status_code=400, detail="Not valid boost")
            
        await redis_cache_tap.update_session_keep_ttl(f"session:{token}", session_state.model_dump())
        
        now = datetime.now()
        result = [{'name': key, 'value': (value - now).total_seconds() if value else 0 } for key, value in data_attr.items()]
        
        return {
            "status": "success",
            "attrs": result,
            **session_state.game_state.model_dump()
        }
    
    finally:
        try:
            await lock.release()
        except:
            pass
    
    raise HTTPException(status_code=400, detail="Error boost")
    
        
# Получение diamonds в dps
@router.get("/tap/claim_diamonds", response_class=JSONResponse)
async def claim_diamonds(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user: Optional[Users] = Depends(get_current_user)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    token = credentials.credentials
    
    session_data = await redis_cache_tap.get_data(f"session:{token}")
    if not session_data:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    session_data['game_state']['player'].update({
        'current_energy':user.current_energy,
        '_last_used_diamonds_dps': user.last_used_diamonds_dps,
        '_speed_diamonds_dps': user.weapon.dps,
        '_last_energy_update': user.time_for_max_energy or datetime.now()
    })
    session_state = SessionStateModel(**session_data)
    
    # Защита от DDoS: ограничение частоты запросов
    current_time = time.time()
    if (current_time - session_state.last_action) < 0.1:
        raise HTTPException(status_code=429, detail="Too many requests")
    
    lock_key = f"user_tap_lock:{user.id}"
    lock = redis_cache_tap.redis.lock(lock_key, timeout=3, blocking_timeout=2)
    
    try:
        # Пытаемся получить блокировку
        if not await lock.acquire():
            raise HTTPException(status_code=429, detail="Please wait, processing previous request")
            
        session_state.last_action = current_time
        
        add_diamonds = session_state.game_state.player.get_diamonds_dps
        diamonds = await sql_credit_diamonds_dps_user(user.id, add_diamonds, session_state.game_state.player)
        
        await redis_cache_tap.update_session_keep_ttl(f"session:{token}", session_state.model_dump())
    
        return {
            "status": "success",
            'diamonds': diamonds
        }
    
    finally:
        try:
            await lock.release()
        except:
            pass
            
    raise HTTPException(status_code=400, detail="Error claim")
    
            

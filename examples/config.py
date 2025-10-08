from dataclasses import dataclass
from typing import Dict, Any
import os
from dotenv import load_dotenv


load_dotenv()

@dataclass
class Config:
    # Секретные данные должны загружаться из переменных окружения
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    PAYMENT_PROVIDER_TOKEN = os.getenv('PAYMENT_PROVIDER_TOKEN')
    SUBSCRIPTION_BOT_TOKEN = os.getenv('SUBSCRIPTION_TELEGRAM_BOT_TOKEN')
    AUTH_DATA = {
        'secret_key': os.getenv('JWT_SECRET_KEY'),
        'algorithm': 'HS256',
        'access_token_expire_minutes': 30 * 24 * 60
    }
    
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CONFIG = {
        'socket_timeout': 5.0,
        'socket_connect_timeout': 5.0,
        'retry_on_timeout': True,
        'max_connections': 10
    }
    RANK_TTL: int = 60 # 1 минута
    
    TELEGRAM_CHANNEL = 'https://t.me/bubble_farm_channel'
    STEAM_API_KEY = os.getenv('STEAM_API_KEY')
    
    BASE_EXP = 2500
    # BASE_ENEMY_LIFETIME = 5000
    BASE_ENEMY_EXP = 100
    # BASE_SPAWN_INTERVAL = 1400
    BASE_PLAYER_DAMAGE = 15
    ENEMY_LIFETIME = 3_000
    SPAWN_INTERVAL = 2_000
    
    GROWTH_FACTOR_LEVEL = 1.15
    # GROWTH_FACTOR_ENEMY_LIFETIME = 1.022
    GROWTH_FACTOR_ENEMY_EXP = 1.05
    # GROWTH_FACTOR_SPAWN_INTERVAL = 1.015
    GROWTH_FACTOR_PLAYER_DAMAGE = 1.08
    
    VOLUME_DIAMONDS_FACTOR = 3
    BASE_VOLUME_DIAMONDS = 2_000
    
    RANGE_DAMAGE_FOR_PLAYER = 4
    BASE_TAP = 10
    ADD_TAP = 2
    
    FACTOR_LUCK = 10
    
    TASKS_TYPES = {
        "break_cases": "combo",
        "cause_damage": "score",
        "earn_experience": "exp"
    }
    
    ROUND_DURATION = 30  # Длительность раунда в секундах
    BETS_TTL = ROUND_DURATION * 2 # Время жизни bets и total_bets
    
    RARITY_CASE = {
        'mil-spec': 0.8,
        'restricted': 0.16,
        'classified': 0.032,
        'covert': 0.0064,
        'rare': 0.00016
    }
    
    RARITY_CASE_WITH_RARE = {
        'classified': 0.9,
        'covert': 0.0936,
        'rare': 0.0064
    }
    
    RARITY_COLLECTION = {
        'consumer': 0.45,
        'industrial': 0.25,
        'mil-spec': 0.2,
        'restricted': 0.06044,
        'classified': 0.032,
        'covert': 0.0064,
        'rare': 0.00016
    }
    
    RARITY_PERSON = {
        'Distinguished': 0.8,
        'Exceptional': 0.16,
        'Superior': 0.032,
        'Master': 0.008  
    }
    
    BG_RARITY = {
        'contraband': '#e77827',
        'rare': '#f6de22', 
        'covert': '#F6222D',
        'classified': '#BB1A8E',
        'restricted': '#be1984', 
        'mil-spec': '#19549b',
        'industrial': '#197c9b',
        'consumer': '#b4d9e9',
        'Distinguished': '#19549b',
        'Exceptional': '#be1984',
        'Superior': '#BB1A8E',
        'Master': '#F6222D'
    }
    
    COLOR_RARITY = {
        'contraband': 'orange',
        'rare': 'yellow', 
        'covert': 'red',
        'classified': 'pink',
        'restricted': 'purple', 
        'mil-spec': 'blue',
        'industrial': 'sky',
        'consumer': 'gray'
    }
    
    AVATAR_OUTLINE_COLORS = {
        'TOP-10 | Outline': 'bg-gradient-to-br from-amber-400 to-amber-600',
        'TOP-30 | Outline': 'bg-gradient-to-br from-purple-400 to-purple-600',
        'TOP-100 | Outline': 'bg-gradient-to-br from-blue-400 to-blue-600',
        'Gray | Outline': 'bg-gray-400',
        'Green | Outline': 'bg-gradient-to-br from-green-400 to-green-600',
        'Teal | Outline': 'bg-gradient-to-br from-teal-400 to-teal-600',
        'Cyan | Outline': 'bg-gradient-to-br from-cyan-400 to-cyan-600',
        'Indigo | Outline': 'bg-gradient-to-br from-indigo-400 to-indigo-600',
        'Violet | Outline': 'bg-gradient-to-br from-violet-400 to-violet-600',
        'Fuchsia | Outline': 'bg-gradient-to-br from-fuchsia-400 to-fuchsia-600',
        'Rose | Outline': 'bg-gradient-to-br from-rose-400 to-rose-600',
        'YRP | Outline': 'bg-gradient-to-br from-yellow-400 via-red-500 to-pink-500',
        'VIP | Outline': 'bg-gradient-to-br from-yellow-400 via-amber-500 to-orange-500',
        'Sponsor | Outline': 'bg-gradient-to-br from-emerald-400 via-teal-500 to-blue-500',
        'Elite | Outline': 'bg-gradient-to-br from-purple-500 via-pink-500 to-red-500',
        'Legend | Outline': 'bg-gradient-to-br from-amber-200 via-amber-400 to-amber-600',
        'Mistic | Outline': 'bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500'
    }
    
    THRESHOLDS_AVATAR_OUTLINE_COLORS_FOR_LEVEL = {
        1: 'Gray | Outline',
        3: 'Green | Outline',
        10: 'Teal | Outline',
        20: 'Cyan | Outline',
        30: 'Indigo | Outline',
        42: 'Violet | Outline',
        53: 'Fuchsia | Outline',
        70: 'Rose | Outline',
        99: 'YRP | Outline'
    }    
        
    REWARDS_FOR_LEVELS = [
        {
            "level": 1,
            "name": "Desert Eagle",
            "type": "weapon",
            "image": "Desert_Eagle_Blue_Ply",
            "id": 308
        },
        {
            "level": 3,
            "name": "Outline",
            "type": "outline",
            "id": 9071
        },
        {
            "level": 5,
            "name": "FAMAS",
            "type": "weapon",
            "image": "FAMAS_Yeti_Camo",
            "id": 2890
        },
        {
            "level": 7,
            "name": "Tickets",
            "type": "currency",
            "amount": 5,
            "currency": "tickets",
        },
        {
            "level": 10,
            "name": "Outline",
            "type": "outline",
            "id": 9064
        },
        {
            "level": 13,
            "name": "Diamonds",
            "type": "currency",
            "amount": 5000,
            "currency": "diamonds",
        },
        {
            "level": 17,
            "name": "Avatar",
            "type": "person",
            "image": "Agent_Col._Mangos_Dabisi",
            "id": 9062
        },
        {
            "level": 20,
            "name": "Outline",
            "type": "outline",
            "id": 9065
        },
        {
            "level": 25,
            "name": "Tickets",
            "type": "currency",
            "amount": 10,
            "currency": "tickets",
        },
        {
            "level": 30,
            "name": "Outline",
            "type": "outline",
            "id": 9066
        },
        {
            "level": 33,
            "name": "AK-47",
            "type": "weapon",
            "image": "AK-47_Wasteland_Rebel",
            "id": 2045
        },
        {
            "level": 38,
            "name": "Avatar",
            "type": "person",
            "image": "Agent_Col._Mangos_Dabisi",
            "id": 9062
        },
        {
            "level": 42,
            "name": "Outline",
            "type": "outline",
            "id": 9067
        },
        {
            "level": 47,
            "name": "Tickets",
            "type": "currency",
            "amount": 25,
            "currency": "tickets",
        },
        {
            "level": 53,
            "name": "Outline",
            "type": "outline",
            "id": 9068
        },
        {
            "level": 58,
            "name": "Bowie Knife",
            "type": "weapon",
            "image": "Bowie_Knife_Bright_Water",
            "id": 6831
        },
        {
            "level": 65,
            "name": "Diamonds",
            "type": "currency",
            "amount": 100_000,
            "currency": "diamonds",
        },
        {
            "level": 70,
            "name": "Outline",
            "type": "outline",
            "id": 9069
        },
        {
            "level": 78,
            "name": "Tickets",
            "type": "currency",
            "amount": 100,
            "currency": "tickets"
        },
        {
            "level": 81,
            "name": "Avatar",
            "type": "person",
            "image": "Agent_Col._Mangos_Dabisi",
            "id": 9062
        },
        {
            "level": 90,
            "name": "Tickets",
            "type": "currency",
            "amount": 125,
            "currency": "tickets",
        },
        {
            "level": 99,
            "name": "Outline",
            "type": "outline",
            "id": 9070
        }
    ]
    
    LEVELS_REWARDS = [reward['level'] for reward in REWARDS_FOR_LEVELS]
    LEN_REWARDS_FOR_LEVELS = len(REWARDS_FOR_LEVELS)
    
    @classmethod
    def get_outline_for_level(cls, level: int) -> str:
        """Возвращает класс Tailwind для outline аватара в зависимости от уровня"""
        selected_style = 'Gray | Outline'  # значение по умолчанию
        
        for threshold, style_key in cls.THRESHOLDS_AVATAR_OUTLINE_COLORS_FOR_LEVEL.items():
            if level >= threshold:
                selected_style = style_key
                
            else:
                break
        
        return cls.AVATAR_OUTLINE_COLORS.get(selected_style, cls.AVATAR_OUTLINE_COLORS['Gray | Outline'])
        
    
    @classmethod
    def get_completed_levels(cls, level: int) -> int:
        """Возвращает кол-во пройденных уровней"""
        count_completed = 0
        
        for threshold in cls.LEVELS_REWARDS:
            if level >= threshold:
                count_completed += 1
                
            else:
                break
        
        return count_completed
        
        
    @classmethod
    def xp_for_level(cls, level: int) -> int:
        """Возвращает опыт для повышения уровня в зависимости от уровня"""
        if level < 1:
            return 0
        
        return int(cls.BASE_EXP * (cls.GROWTH_FACTOR_LEVEL ** (level - 1)))
        

    @staticmethod
    def _init_calculate_enemy_health(BASE_PLAYER_DAMAGE: int, RANGE_DAMAGE_FOR_PLAYER: int, GROWTH_FACTOR_PLAYER_DAMAGE: float, max_level: int) -> Dict[int, int]:
        result = {}
        """Формула здоровья врага (растет с уровнем героя)"""
        for lvl in range(0, max_level + 1):
            level = lvl
            if level < (1 + RANGE_DAMAGE_FOR_PLAYER):
                level = 1 + RANGE_DAMAGE_FOR_PLAYER
            
            level_factor = GROWTH_FACTOR_PLAYER_DAMAGE ** (level - 1 - RANGE_DAMAGE_FOR_PLAYER)
            result[lvl] = int(BASE_PLAYER_DAMAGE * level_factor)

        return result
    
    
    PLAYER_DAMAGE_FOR_LEVEL = _init_calculate_enemy_health(
        BASE_PLAYER_DAMAGE,
        RANGE_DAMAGE_FOR_PLAYER, 
        GROWTH_FACTOR_PLAYER_DAMAGE, 
        100
    )
    
    
    @staticmethod
    def _init_tap_range_levels(BASE_TAP: int, ADD_TAP: int, RANGE_DAMAGE_FOR_PLAYER: int):
        return {i: BASE_TAP + ADD_TAP*i for i in range(RANGE_DAMAGE_FOR_PLAYER + 1)}
        
        
    TAP_FOR_RANGE_LEVEL = _init_tap_range_levels(
        BASE_TAP, 
        ADD_TAP,
        RANGE_DAMAGE_FOR_PLAYER
    )
    
    @classmethod
    def calculate_volume_diamonds(cls, level: int) -> int:
        return ((level // cls.VOLUME_DIAMONDS_FACTOR) + 1) * cls.BASE_VOLUME_DIAMONDS
        
    @classmethod
    def calculate_enemy_health_adjustment(cls, level: int, level_weapon: int) -> int:
        """Корректировка здоровья врага"""
        level_range = level - level_weapon
        
        return cls.PLAYER_DAMAGE_FOR_LEVEL[level_weapon] * cls.TAP_FOR_RANGE_LEVEL[level_range]
    
    # @classmethod
    # def calculate_enemy_lifetime(cls, level: int) -> int:
        """Формула времени жизни врага (уменьшается с уровнем героя)"""
        # level_factor = cls.GROWTH_FACTOR_ENEMY_LIFETIME ** (level - 1)
        # return int(max(1000, cls.BASE_ENEMY_LIFETIME / level_factor))  # Не менее 1 секунды
            

    @classmethod
    def calculate_enemy_exp(cls, level: int) -> int:
        """Формула опыта за убийство врага"""
        level_factor = cls.GROWTH_FACTOR_ENEMY_EXP ** (level - 1)
        return int(cls.BASE_ENEMY_EXP * level_factor)
        
    
    # @classmethod
    # def calculate_spawn_interval(cls, level: int) -> int:
        """Формула интервала появления врагов (уменьшается с уровнем)"""
        # return int(max(500, cls.BASE_SPAWN_INTERVAL / (cls.GROWTH_FACTOR_SPAWN_INTERVAL ** (level - 1))))  # Не менее 0.5 секунды
    
    
    @classmethod
    def adjust_probabilities_with_luck(cls, base_probs: dict, luck: float):
        # Копируем вероятности
        adjusted = base_probs.copy()
       
        # 1. Определяем группы редкостей
        rare = ['classified', 'covert', 'rare']
        common = [key for key in base_probs if key not in rare]
        
        # 2. Вычисляем исходную сумму вероятностей для каждой группы
        total_common = sum(base_probs[r] for r in common)
        total_rare = sum(base_probs[r] for r in rare)
        
        # 3. Увеличиваем редкие предметы (нелинейно, чтобы rare получал больше)
        boost_factor = 1 + (luck / 100) * cls.FACTOR_LUCK
        
        for rarity in rare:
            adjusted[rarity] *= boost_factor
        
        # 4. Вычисляем сколько вероятности добавили к редким
        added_prob = sum(adjusted[r] for r in rare) - total_rare
       
        # 5. Уменьшаем обычные предметы пропорционально их исходному весу
        for rarity in common:
            # Уменьшаем пропорционально исходной вероятности
            reduction_ratio = base_probs[rarity] / total_common
            adjusted[rarity] -= added_prob * reduction_ratio
        
        # 6. Нормализуем (на случай погрешностей)
        total = sum(adjusted.values())
        return {k: v / total for k, v in adjusted.items()}
        

_instance = None

def get_config() -> Config:
    global _instance
    if _instance is None:
        _instance = Config()
        
    return _instance
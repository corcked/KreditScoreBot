from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Dict, Any

from src.core.enums import (
    Gender,
    MaritalStatus,
    Education,
    HousingStatus,
    Region,
    DeviceType,
)


@dataclass
class PersonalData:
    """Персональные данные для расчета скоринга"""
    age: Optional[int] = None
    gender: Optional[Gender] = None
    work_experience_months: Optional[int] = None
    address_stability_years: Optional[int] = None
    housing_status: Optional[HousingStatus] = None
    marital_status: Optional[MaritalStatus] = None
    education: Optional[Education] = None
    closed_loans_count: Optional[int] = None
    has_other_loans: bool = False
    pdn_with_other_loans: Optional[Decimal] = None
    region: Optional[Region] = None
    device_type: Optional[DeviceType] = None
    referral_count: int = 0


class ScoringCalculator:
    """Калькулятор скоринг-балла"""

    # Базовый балл
    BASE_SCORE = 600
    MIN_SCORE = 300
    MAX_SCORE = 900

    # Веса для каждого параметра
    SCORING_WEIGHTS = {
        "age": {
            "condition": lambda age: age >= 35,
            "points": 70,
            "description": "Возраст ≥ 35 лет"
        },
        "gender": {
            "condition": lambda gender: gender == Gender.FEMALE,
            "points": 20,
            "description": "Женский пол"
        },
        "work_experience": {
            "condition": lambda months: months >= 24,
            "points": 20,
            "description": "Стаж работы ≥ 24 месяцев"
        },
        "address_stability": {
            "condition": lambda years: years >= 3,
            "points": 30,
            "description": "Проживание по адресу ≥ 3 лет"
        },
        "housing": {
            "condition": lambda status: status == HousingStatus.OWN,
            "points": 20,
            "description": "Собственное жилье без ипотеки"
        },
        "marital": {
            "condition": lambda status: status == MaritalStatus.MARRIED,
            "points": 10,
            "description": "Женат/замужем"
        },
        "education": {
            "condition": lambda edu: edu == Education.HIGHER,
            "points": 20,
            "description": "Высшее образование"
        },
        "closed_loans": {
            "condition": lambda count: count >= 3,
            "points": 20,
            "description": "Закрытых займов ≥ 3"
        },
        "other_loans_ok": {
            "condition": lambda pdn: pdn is not None and pdn <= 50,
            "points": 30,
            "description": "Есть другие кредиты, но ПДН ≤ 50%"
        },
        "region": {
            "condition": lambda region: region in [Region.TASHKENT, Region.TASHKENT_REGION],
            "points": 20,
            "description": "Ташкент или Ташкентская область"
        },
        "device": {
            "condition": lambda device: device == DeviceType.APPLE,
            "points": 20,
            "description": "Устройство Apple"
        }
    }

    # Бонус за реферала
    REFERRAL_BONUS = 20

    @classmethod
    def calculate_score(cls, data: PersonalData) -> int:
        """
        Расчет скоринг-балла по формуле:
        score = CLAMP(600 + Σ баллы, 300, 900)
        
        Args:
            data: Персональные данные пользователя
            
        Returns:
            Скоринг-балл (от 300 до 900)
        """
        total_points = 0

        # Подсчет баллов за персональные данные
        if data.age is not None and cls.SCORING_WEIGHTS["age"]["condition"](data.age):
            total_points += cls.SCORING_WEIGHTS["age"]["points"]

        if data.gender is not None and cls.SCORING_WEIGHTS["gender"]["condition"](data.gender):
            total_points += cls.SCORING_WEIGHTS["gender"]["points"]

        if data.work_experience_months is not None and cls.SCORING_WEIGHTS["work_experience"]["condition"](data.work_experience_months):
            total_points += cls.SCORING_WEIGHTS["work_experience"]["points"]

        if data.address_stability_years is not None and cls.SCORING_WEIGHTS["address_stability"]["condition"](data.address_stability_years):
            total_points += cls.SCORING_WEIGHTS["address_stability"]["points"]

        if data.housing_status is not None and cls.SCORING_WEIGHTS["housing"]["condition"](data.housing_status):
            total_points += cls.SCORING_WEIGHTS["housing"]["points"]

        if data.marital_status is not None and cls.SCORING_WEIGHTS["marital"]["condition"](data.marital_status):
            total_points += cls.SCORING_WEIGHTS["marital"]["points"]

        if data.education is not None and cls.SCORING_WEIGHTS["education"]["condition"](data.education):
            total_points += cls.SCORING_WEIGHTS["education"]["points"]

        if data.closed_loans_count is not None and cls.SCORING_WEIGHTS["closed_loans"]["condition"](data.closed_loans_count):
            total_points += cls.SCORING_WEIGHTS["closed_loans"]["points"]

        # Проверка других кредитов
        if data.has_other_loans and data.pdn_with_other_loans is not None:
            if cls.SCORING_WEIGHTS["other_loans_ok"]["condition"](data.pdn_with_other_loans):
                total_points += cls.SCORING_WEIGHTS["other_loans_ok"]["points"]

        if data.region is not None and cls.SCORING_WEIGHTS["region"]["condition"](data.region):
            total_points += cls.SCORING_WEIGHTS["region"]["points"]

        if data.device_type is not None and cls.SCORING_WEIGHTS["device"]["condition"](data.device_type):
            total_points += cls.SCORING_WEIGHTS["device"]["points"]

        # Бонусы за рефералов
        referral_points = data.referral_count * cls.REFERRAL_BONUS

        # Итоговый расчет с ограничениями
        raw_score = cls.BASE_SCORE + total_points + referral_points
        return max(cls.MIN_SCORE, min(cls.MAX_SCORE, raw_score))

    @classmethod
    def get_score_breakdown(cls, data: PersonalData) -> Dict[str, Any]:
        """
        Получение детализации скоринг-балла
        
        Args:
            data: Персональные данные
            
        Returns:
            Словарь с детализацией баллов
        """
        breakdown = {
            "base_score": cls.BASE_SCORE,
            "components": [],
            "referral_bonus": 0,
            "total_score": 0
        }

        # Проверка каждого компонента
        if data.age is not None and cls.SCORING_WEIGHTS["age"]["condition"](data.age):
            breakdown["components"].append({
                "name": cls.SCORING_WEIGHTS["age"]["description"],
                "points": cls.SCORING_WEIGHTS["age"]["points"]
            })

        if data.gender is not None and cls.SCORING_WEIGHTS["gender"]["condition"](data.gender):
            breakdown["components"].append({
                "name": cls.SCORING_WEIGHTS["gender"]["description"],
                "points": cls.SCORING_WEIGHTS["gender"]["points"]
            })

        if data.work_experience_months is not None and cls.SCORING_WEIGHTS["work_experience"]["condition"](data.work_experience_months):
            breakdown["components"].append({
                "name": cls.SCORING_WEIGHTS["work_experience"]["description"],
                "points": cls.SCORING_WEIGHTS["work_experience"]["points"]
            })

        if data.address_stability_years is not None and cls.SCORING_WEIGHTS["address_stability"]["condition"](data.address_stability_years):
            breakdown["components"].append({
                "name": cls.SCORING_WEIGHTS["address_stability"]["description"],
                "points": cls.SCORING_WEIGHTS["address_stability"]["points"]
            })

        if data.housing_status is not None and cls.SCORING_WEIGHTS["housing"]["condition"](data.housing_status):
            breakdown["components"].append({
                "name": cls.SCORING_WEIGHTS["housing"]["description"],
                "points": cls.SCORING_WEIGHTS["housing"]["points"]
            })

        if data.marital_status is not None and cls.SCORING_WEIGHTS["marital"]["condition"](data.marital_status):
            breakdown["components"].append({
                "name": cls.SCORING_WEIGHTS["marital"]["description"],
                "points": cls.SCORING_WEIGHTS["marital"]["points"]
            })

        if data.education is not None and cls.SCORING_WEIGHTS["education"]["condition"](data.education):
            breakdown["components"].append({
                "name": cls.SCORING_WEIGHTS["education"]["description"],
                "points": cls.SCORING_WEIGHTS["education"]["points"]
            })

        if data.closed_loans_count is not None and cls.SCORING_WEIGHTS["closed_loans"]["condition"](data.closed_loans_count):
            breakdown["components"].append({
                "name": cls.SCORING_WEIGHTS["closed_loans"]["description"],
                "points": cls.SCORING_WEIGHTS["closed_loans"]["points"]
            })

        if data.has_other_loans and data.pdn_with_other_loans is not None:
            if cls.SCORING_WEIGHTS["other_loans_ok"]["condition"](data.pdn_with_other_loans):
                breakdown["components"].append({
                    "name": cls.SCORING_WEIGHTS["other_loans_ok"]["description"],
                    "points": cls.SCORING_WEIGHTS["other_loans_ok"]["points"]
                })

        if data.region is not None and cls.SCORING_WEIGHTS["region"]["condition"](data.region):
            breakdown["components"].append({
                "name": cls.SCORING_WEIGHTS["region"]["description"],
                "points": cls.SCORING_WEIGHTS["region"]["points"]
            })

        if data.device_type is not None and cls.SCORING_WEIGHTS["device"]["condition"](data.device_type):
            breakdown["components"].append({
                "name": cls.SCORING_WEIGHTS["device"]["description"],
                "points": cls.SCORING_WEIGHTS["device"]["points"]
            })

        # Рефералы
        if data.referral_count > 0:
            referral_bonus = data.referral_count * cls.REFERRAL_BONUS
            breakdown["referral_bonus"] = referral_bonus
            breakdown["components"].append({
                "name": f"Рефералы ({data.referral_count} чел.)",
                "points": referral_bonus
            })

        # Итоговый балл
        breakdown["total_score"] = cls.calculate_score(data)
        return breakdown

    @classmethod
    def get_score_level(cls, score: int) -> str:
        """Определение уровня скоринга"""
        if score >= 800:
            return "Отличный"
        elif score >= 700:
            return "Хороший"
        elif score >= 600:
            return "Средний"
        elif score >= 500:
            return "Ниже среднего"
        else:
            return "Низкий"

    @classmethod
    def get_completion_percentage(cls, data: PersonalData) -> int:
        """
        Расчет процента заполненности профиля
        
        Returns:
            Процент заполненности (0-100)
        """
        fields = [
            data.age,
            data.gender,
            data.work_experience_months,
            data.address_stability_years,
            data.housing_status,
            data.marital_status,
            data.education,
            data.closed_loans_count,
            data.region,
            data.device_type
        ]
        
        filled = sum(1 for field in fields if field is not None)
        return int((filled / len(fields)) * 100)

    @classmethod
    def format_score_message(cls, score: int, breakdown: Dict[str, Any]) -> str:
        """Форматирование сообщения со скорингом для пользователя"""
        level = cls.get_score_level(score)
        
        message = f"📊 **Ваш скоринг-балл: {score}**\\n"
        message += f"Уровень: {level}\\n\\n"
        
        if breakdown["components"]:
            message += "**Детализация:**\\n"
            for component in breakdown["components"]:
                message += f"✅ {component['name']}: +{component['points']}\\n"
        
        return message
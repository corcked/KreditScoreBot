from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Dict, Any, Callable

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
            "description": "Age ≥ 35 years",
            "description_key": "Age ≥ 35 years"
        },
        "gender": {
            "condition": lambda gender: gender == Gender.FEMALE,
            "points": 20,
            "description": "Female gender",
            "description_key": "Female gender"
        },
        "work_experience": {
            "condition": lambda months: months >= 24,
            "points": 20,
            "description": "Work experience ≥ 24 months",
            "description_key": "Work experience ≥ 24 months"
        },
        "address_stability": {
            "condition": lambda years: years >= 3,
            "points": 30,
            "description": "Living at address ≥ 3 years",
            "description_key": "Living at address ≥ 3 years"
        },
        "housing": {
            "condition": lambda status: status == HousingStatus.OWN,
            "points": 20,
            "description": "Own home without mortgage",
            "description_key": "Own home without mortgage"
        },
        "marital": {
            "condition": lambda status: status == MaritalStatus.MARRIED,
            "points": 10,
            "description": "Married",
            "description_key": "Married"
        },
        "education": {
            "condition": lambda edu: edu == Education.HIGHER,
            "points": 20,
            "description": "Higher education",
            "description_key": "Higher education"
        },
        "closed_loans": {
            "condition": lambda count: count >= 3,
            "points": 20,
            "description": "Closed loans ≥ 3",
            "description_key": "Closed loans ≥ 3"
        },
        "other_loans_ok": {
            "condition": lambda pdn: pdn is not None and pdn <= 50,
            "points": 30,
            "description": "Has other loans but DTI ≤ 50%",
            "description_key": "Has other loans but DTI ≤ 50%"
        },
        "region": {
            "condition": lambda region: region in [Region.TASHKENT, Region.TASHKENT_REGION],
            "points": 20,
            "description": "Tashkent or Tashkent region",
            "description_key": "Tashkent or Tashkent region"
        },
        "device": {
            "condition": lambda device: device == DeviceType.APPLE,
            "points": 20,
            "description": "Apple device",
            "description_key": "Apple device"
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
    def get_score_breakdown(cls, data: PersonalData, translate: Optional[Callable[[str], str]] = None) -> Dict[str, Any]:
        """
        Получение детализации скоринг-балла
        
        Args:
            data: Персональные данные
            translate: Функция перевода (опционально)
            
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
            desc = translate(cls.SCORING_WEIGHTS["age"]["description_key"]) if translate else cls.SCORING_WEIGHTS["age"]["description"]
            breakdown["components"].append({
                "name": desc,
                "points": cls.SCORING_WEIGHTS["age"]["points"]
            })

        if data.gender is not None and cls.SCORING_WEIGHTS["gender"]["condition"](data.gender):
            desc = translate(cls.SCORING_WEIGHTS["gender"]["description_key"]) if translate else cls.SCORING_WEIGHTS["gender"]["description"]
            breakdown["components"].append({
                "name": desc,
                "points": cls.SCORING_WEIGHTS["gender"]["points"]
            })

        if data.work_experience_months is not None and cls.SCORING_WEIGHTS["work_experience"]["condition"](data.work_experience_months):
            desc = translate(cls.SCORING_WEIGHTS["work_experience"]["description_key"]) if translate else cls.SCORING_WEIGHTS["work_experience"]["description"]
            breakdown["components"].append({
                "name": desc,
                "points": cls.SCORING_WEIGHTS["work_experience"]["points"]
            })

        if data.address_stability_years is not None and cls.SCORING_WEIGHTS["address_stability"]["condition"](data.address_stability_years):
            desc = translate(cls.SCORING_WEIGHTS["address_stability"]["description_key"]) if translate else cls.SCORING_WEIGHTS["address_stability"]["description"]
            breakdown["components"].append({
                "name": desc,
                "points": cls.SCORING_WEIGHTS["address_stability"]["points"]
            })

        if data.housing_status is not None and cls.SCORING_WEIGHTS["housing"]["condition"](data.housing_status):
            desc = translate(cls.SCORING_WEIGHTS["housing"]["description_key"]) if translate else cls.SCORING_WEIGHTS["housing"]["description"]
            breakdown["components"].append({
                "name": desc,
                "points": cls.SCORING_WEIGHTS["housing"]["points"]
            })

        if data.marital_status is not None and cls.SCORING_WEIGHTS["marital"]["condition"](data.marital_status):
            desc = translate(cls.SCORING_WEIGHTS["marital"]["description_key"]) if translate else cls.SCORING_WEIGHTS["marital"]["description"]
            breakdown["components"].append({
                "name": desc,
                "points": cls.SCORING_WEIGHTS["marital"]["points"]
            })

        if data.education is not None and cls.SCORING_WEIGHTS["education"]["condition"](data.education):
            desc = translate(cls.SCORING_WEIGHTS["education"]["description_key"]) if translate else cls.SCORING_WEIGHTS["education"]["description"]
            breakdown["components"].append({
                "name": desc,
                "points": cls.SCORING_WEIGHTS["education"]["points"]
            })

        if data.closed_loans_count is not None and cls.SCORING_WEIGHTS["closed_loans"]["condition"](data.closed_loans_count):
            desc = translate(cls.SCORING_WEIGHTS["closed_loans"]["description_key"]) if translate else cls.SCORING_WEIGHTS["closed_loans"]["description"]
            breakdown["components"].append({
                "name": desc,
                "points": cls.SCORING_WEIGHTS["closed_loans"]["points"]
            })

        if data.has_other_loans and data.pdn_with_other_loans is not None:
            if cls.SCORING_WEIGHTS["other_loans_ok"]["condition"](data.pdn_with_other_loans):
                desc = translate(cls.SCORING_WEIGHTS["other_loans_ok"]["description_key"]) if translate else cls.SCORING_WEIGHTS["other_loans_ok"]["description"]
                breakdown["components"].append({
                    "name": desc,
                    "points": cls.SCORING_WEIGHTS["other_loans_ok"]["points"]
                })

        if data.region is not None and cls.SCORING_WEIGHTS["region"]["condition"](data.region):
            desc = translate(cls.SCORING_WEIGHTS["region"]["description_key"]) if translate else cls.SCORING_WEIGHTS["region"]["description"]
            breakdown["components"].append({
                "name": desc,
                "points": cls.SCORING_WEIGHTS["region"]["points"]
            })

        if data.device_type is not None and cls.SCORING_WEIGHTS["device"]["condition"](data.device_type):
            desc = translate(cls.SCORING_WEIGHTS["device"]["description_key"]) if translate else cls.SCORING_WEIGHTS["device"]["description"]
            breakdown["components"].append({
                "name": desc,
                "points": cls.SCORING_WEIGHTS["device"]["points"]
            })

        # Рефералы
        if data.referral_count > 0:
            referral_bonus = data.referral_count * cls.REFERRAL_BONUS
            breakdown["referral_bonus"] = referral_bonus
            if translate:
                name = translate('Referrals ({count} people)').format(count=data.referral_count)
            else:
                name = f"Referrals ({data.referral_count} people)"
            breakdown["components"].append({
                "name": name,
                "points": referral_bonus
            })

        # Итоговый балл
        breakdown["total_score"] = cls.calculate_score(data)
        return breakdown

    @classmethod
    def get_score_level(cls, score: int, translate: Optional[Callable[[str], str]] = None) -> str:
        """Определение уровня скоринга"""
        if score >= 800:
            return translate('Excellent') if translate else 'Excellent'
        elif score >= 700:
            return translate('Good') if translate else 'Good'
        elif score >= 600:
            return translate('Average') if translate else 'Average'
        elif score >= 500:
            return translate('Below average') if translate else 'Below average'
        else:
            return translate('Low') if translate else 'Low'

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
    def format_score_message(cls, score: int, breakdown: Dict[str, Any], translate: Optional[Callable[[str], str]] = None) -> str:
        """Форматирование сообщения со скорингом для пользователя"""
        level = cls.get_score_level(score, translate)
        
        if translate:
            message = f"📊 **{translate('Your credit score: {score}').format(score=score)}**\\n"
            message += f"{translate('Level: {level}').format(level=level)}\\n\\n"
            
            if breakdown["components"]:
                message += f"**{translate('Breakdown:')}**\\n"
                for component in breakdown["components"]:
                    message += f"✅ {component['name']}: +{component['points']}\\n"
        else:
            message = f"📊 **Your credit score: {score}**\\n"
            message += f"Level: {level}\\n\\n"
            
            if breakdown["components"]:
                message += "**Breakdown:**\\n"
                for component in breakdown["components"]:
                    message += f"✅ {component['name']}: +{component['points']}\\n"
        
        return message
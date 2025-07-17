import pytest
from decimal import Decimal

from src.core.enums import (
    DeviceType,
    Education,
    Gender,
    HousingStatus,
    MaritalStatus,
    Region,
)
from src.core.scoring import PersonalData, ScoringCalculator


class TestScoringCalculator:
    """Тесты для калькулятора скоринга"""

    def test_calculate_score_empty_data(self):
        """Тест расчета с пустыми данными"""
        data = PersonalData()
        score = ScoringCalculator.calculate_score(data)
        
        # Базовый балл без бонусов
        assert score == 600

    def test_calculate_score_age_bonus(self):
        """Тест бонуса за возраст"""
        data = PersonalData(age=35)
        score = ScoringCalculator.calculate_score(data)
        assert score == 670  # 600 + 70
        
        data = PersonalData(age=34)
        score = ScoringCalculator.calculate_score(data)
        assert score == 600  # Нет бонуса

    def test_calculate_score_gender_bonus(self):
        """Тест бонуса за пол"""
        data = PersonalData(gender=Gender.FEMALE)
        score = ScoringCalculator.calculate_score(data)
        assert score == 620  # 600 + 20
        
        data = PersonalData(gender=Gender.MALE)
        score = ScoringCalculator.calculate_score(data)
        assert score == 600  # Нет бонуса

    def test_calculate_score_work_experience(self):
        """Тест бонуса за стаж работы"""
        data = PersonalData(work_experience_months=24)
        score = ScoringCalculator.calculate_score(data)
        assert score == 620  # 600 + 20
        
        data = PersonalData(work_experience_months=23)
        score = ScoringCalculator.calculate_score(data)
        assert score == 600  # Нет бонуса

    def test_calculate_score_region_bonus(self):
        """Тест бонуса за регион"""
        data = PersonalData(region=Region.TASHKENT)
        score = ScoringCalculator.calculate_score(data)
        assert score == 620  # 600 + 20
        
        data = PersonalData(region=Region.TASHKENT_REGION)
        score = ScoringCalculator.calculate_score(data)
        assert score == 620  # 600 + 20
        
        data = PersonalData(region=Region.ANDIJAN)
        score = ScoringCalculator.calculate_score(data)
        assert score == 600  # Нет бонуса

    def test_calculate_score_education(self):
        """Тест бонуса за образование"""
        data = PersonalData(education=Education.HIGHER)
        score = ScoringCalculator.calculate_score(data)
        assert score == 620  # 600 + 20
        
        data = PersonalData(education=Education.SECONDARY)
        score = ScoringCalculator.calculate_score(data)
        assert score == 600  # Нет бонуса

    def test_calculate_score_referrals(self):
        """Тест бонуса за рефералов"""
        data = PersonalData(referral_count=1)
        score = ScoringCalculator.calculate_score(data)
        assert score == 620  # 600 + 20
        
        data = PersonalData(referral_count=5)
        score = ScoringCalculator.calculate_score(data)
        assert score == 700  # 600 + 100

    def test_calculate_score_other_loans(self):
        """Тест бонуса за другие кредиты с хорошим ПДН"""
        data = PersonalData(
            has_other_loans=True,
            pdn_with_other_loans=Decimal("45")
        )
        score = ScoringCalculator.calculate_score(data)
        assert score == 630  # 600 + 30
        
        # ПДН больше 50% - нет бонуса
        data = PersonalData(
            has_other_loans=True,
            pdn_with_other_loans=Decimal("55")
        )
        score = ScoringCalculator.calculate_score(data)
        assert score == 600

    def test_calculate_score_max_limit(self):
        """Тест максимального ограничения скоринга"""
        # Создаем профиль с максимальными бонусами
        data = PersonalData(
            age=40,
            gender=Gender.FEMALE,
            work_experience_months=36,
            address_stability_years=5,
            housing_status=HousingStatus.OWN,
            marital_status=MaritalStatus.MARRIED,
            education=Education.HIGHER,
            closed_loans_count=5,
            has_other_loans=True,
            pdn_with_other_loans=Decimal("30"),
            region=Region.TASHKENT,
            device_type=DeviceType.APPLE,
            referral_count=10  # Много рефералов
        )
        
        score = ScoringCalculator.calculate_score(data)
        assert score == 900  # Ограничен максимумом

    def test_calculate_score_min_limit(self):
        """Тест минимального ограничения скоринга"""
        # В текущей реализации нет отрицательных баллов,
        # поэтому минимум не может быть меньше базового
        data = PersonalData()
        score = ScoringCalculator.calculate_score(data)
        assert score >= 300

    def test_get_score_level(self):
        """Тест определения уровня скоринга"""
        assert ScoringCalculator.get_score_level(850) == "Отличный"
        assert ScoringCalculator.get_score_level(750) == "Хороший"
        assert ScoringCalculator.get_score_level(650) == "Средний"
        assert ScoringCalculator.get_score_level(550) == "Ниже среднего"
        assert ScoringCalculator.get_score_level(450) == "Низкий"

    def test_get_completion_percentage(self):
        """Тест расчета процента заполненности"""
        # Пустой профиль
        data = PersonalData()
        assert ScoringCalculator.get_completion_percentage(data) == 0
        
        # Частично заполненный
        data = PersonalData(
            age=30,
            gender=Gender.MALE,
            education=Education.HIGHER,
            region=Region.TASHKENT,
            device_type=DeviceType.ANDROID
        )
        assert ScoringCalculator.get_completion_percentage(data) == 50
        
        # Полностью заполненный
        data = PersonalData(
            age=30,
            gender=Gender.MALE,
            work_experience_months=24,
            address_stability_years=3,
            housing_status=HousingStatus.OWN,
            marital_status=MaritalStatus.MARRIED,
            education=Education.HIGHER,
            closed_loans_count=2,
            region=Region.TASHKENT,
            device_type=DeviceType.ANDROID
        )
        assert ScoringCalculator.get_completion_percentage(data) == 100

    def test_get_score_breakdown(self):
        """Тест детализации скоринга"""
        data = PersonalData(
            age=40,
            gender=Gender.FEMALE,
            referral_count=2
        )
        
        breakdown = ScoringCalculator.get_score_breakdown(data)
        
        assert breakdown["base_score"] == 600
        assert breakdown["referral_bonus"] == 40
        assert breakdown["total_score"] == 730  # 600 + 70 + 20 + 40
        
        # Проверяем компоненты
        components = breakdown["components"]
        assert len(components) == 3
        
        age_component = next(c for c in components if "35 лет" in c["name"])
        assert age_component["points"] == 70
        
        gender_component = next(c for c in components if "Женский" in c["name"])
        assert gender_component["points"] == 20

    def test_format_score_message(self):
        """Тест форматирования сообщения со скорингом"""
        data = PersonalData(age=40)
        score = ScoringCalculator.calculate_score(data)
        breakdown = ScoringCalculator.get_score_breakdown(data)
        
        message = ScoringCalculator.format_score_message(score, breakdown)
        
        assert "670" in message
        assert "Хороший" in message
        assert "✅" in message
        assert "+70" in message
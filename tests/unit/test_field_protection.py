import pytest
from src.core.field_protection import FieldProtectionManager
from src.db.models import PersonalData
from src.core.enums import Gender, Education, Region, HousingStatus, MaritalStatus


class TestFieldProtectionManager:
    """Тесты менеджера защиты полей"""
    
    def test_is_field_protected_empty_field(self):
        """Тест: пустое поле не защищено"""
        personal_data = PersonalData()
        assert not FieldProtectionManager.is_field_protected(personal_data, 'age')
    
    def test_is_field_protected_filled_field(self):
        """Тест: заполненное защищаемое поле защищено"""
        personal_data = PersonalData(age=30)
        assert FieldProtectionManager.is_field_protected(personal_data, 'age')
    
    def test_is_field_protected_always_editable(self):
        """Тест: всегда редактируемое поле не защищено"""
        personal_data = PersonalData(monthly_income=100000)
        assert not FieldProtectionManager.is_field_protected(personal_data, 'monthly_income')
    
    def test_get_protected_fields_empty_data(self):
        """Тест: пустые данные - нет защищенных полей"""
        personal_data = PersonalData()
        protected = FieldProtectionManager.get_protected_fields(personal_data)
        assert protected == []
    
    def test_get_protected_fields_some_filled(self):
        """Тест: частично заполненные данные"""
        personal_data = PersonalData(
            age=30,
            gender=Gender.FEMALE,
            monthly_income=100000  # Всегда редактируемое
        )
        protected = FieldProtectionManager.get_protected_fields(personal_data)
        assert 'age' in protected
        assert 'gender' in protected
        assert 'monthly_income' not in protected
    
    def test_get_editable_fields(self):
        """Тест: получение редактируемых полей"""
        personal_data = PersonalData(
            age=30,  # Защищено
            monthly_income=100000  # Всегда редактируемо
        )
        editable = FieldProtectionManager.get_editable_fields(personal_data)
        
        # Доход всегда редактируемый
        assert 'monthly_income' in editable
        assert 'has_other_loans' in editable
        assert 'other_loans_monthly_payment' in editable
        
        # Возраст заполнен - не редактируемый
        assert 'age' not in editable
        
        # Пол не заполнен - редактируемый
        assert 'gender' in editable
    
    def test_get_field_status(self):
        """Тест: получение статуса всех полей"""
        personal_data = PersonalData(
            age=30,
            monthly_income=100000
        )
        status = FieldProtectionManager.get_field_status(personal_data)
        
        # Возраст защищен
        assert status['age']['is_protected'] is True
        assert status['age']['is_filled'] is True
        assert status['age']['current_value'] == 30
        
        # Доход не защищен
        assert status['monthly_income']['is_protected'] is False
        assert status['monthly_income']['is_filled'] is True
        assert status['monthly_income']['is_always_editable'] is True
        
        # Пол не заполнен
        assert status['gender']['is_protected'] is False
        assert status['gender']['is_filled'] is False
        assert status['gender']['current_value'] is None
    
    def test_get_protection_reason(self):
        """Тест: получение причины защиты"""
        reason = FieldProtectionManager.get_protection_reason('age')
        assert 'credit score' in reason.lower()
        assert 'reliability' in reason.lower()
    
    def test_all_fields_coverage(self):
        """Тест: все поля покрыты в статусе"""
        personal_data = PersonalData()
        status = FieldProtectionManager.get_field_status(personal_data)
        
        # Проверяем, что все защищенные поля есть в статусе
        for field in FieldProtectionManager.PROTECTED_FIELDS:
            assert field in status
            
        # Проверяем, что все всегда редактируемые поля есть в статусе
        for field in FieldProtectionManager.ALWAYS_EDITABLE_FIELDS:
            assert field in status
    
    def test_field_protection_with_all_data_filled(self):
        """Тест: все защищаемые поля заполнены"""
        personal_data = PersonalData(
            age=30,
            gender=Gender.MALE,
            work_experience_months=24,
            address_stability_years=5,
            housing_status=HousingStatus.OWN,
            marital_status=MaritalStatus.MARRIED,
            education=Education.HIGHER,
            closed_loans_count=2,
            region=Region.TASHKENT,
            monthly_income=500000,
            has_other_loans=True,
            other_loans_monthly_payment=50000
        )
        
        protected = FieldProtectionManager.get_protected_fields(personal_data)
        editable = FieldProtectionManager.get_editable_fields(personal_data)
        
        # Все защищаемые поля должны быть защищены
        assert len(protected) == len(FieldProtectionManager.PROTECTED_FIELDS)
        
        # Только всегда редактируемые поля должны быть доступны
        assert len(editable) == len(FieldProtectionManager.ALWAYS_EDITABLE_FIELDS)
        for field in FieldProtectionManager.ALWAYS_EDITABLE_FIELDS:
            assert field in editable
    
    def test_field_protection_with_translation(self):
        """Тест: проверка с функцией перевода"""
        def mock_translate(text):
            return f"[TRANSLATED] {text}"
        
        reason = FieldProtectionManager.get_protection_reason('age', mock_translate)
        assert reason.startswith("[TRANSLATED]")
        assert "credit score" in reason
    
    def test_unknown_field_protection(self):
        """Тест: неизвестное поле не защищено"""
        personal_data = PersonalData()
        # Неизвестное поле
        assert not FieldProtectionManager.is_field_protected(personal_data, 'unknown_field')
    
    def test_field_status_structure(self):
        """Тест: структура возвращаемого статуса"""
        personal_data = PersonalData(age=25)
        status = FieldProtectionManager.get_field_status(personal_data)
        
        # Проверяем структуру для одного поля
        age_status = status['age']
        assert 'is_protected' in age_status
        assert 'is_filled' in age_status  
        assert 'display_name' in age_status
        assert 'current_value' in age_status
        assert 'is_always_editable' in age_status
        
        # Проверяем корректность значений
        assert age_status['is_protected'] is True
        assert age_status['is_filled'] is True
        assert age_status['current_value'] == 25
        assert age_status['display_name'] == 'Возраст'
        assert age_status['is_always_editable'] is False
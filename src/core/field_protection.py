from typing import List, Dict, Optional
from src.db.models import PersonalData
from src.core.enums import *


class FieldProtectionManager:
    """Менеджер защиты полей от изменения"""
    
    # Поля, которые блокируются после заполнения
    PROTECTED_FIELDS = {
        'age': 'Возраст',
        'gender': 'Пол',
        'work_experience_months': 'Стаж работы',
        'address_stability_years': 'Стабильность адреса',
        'housing_status': 'Статус жилья',
        'marital_status': 'Семейное положение',
        'education': 'Образование',
        'closed_loans_count': 'Количество закрытых займов',
        'region': 'Регион проживания',
    }
    
    # Поля, которые всегда можно редактировать
    ALWAYS_EDITABLE_FIELDS = {
        'monthly_income': 'Ежемесячный доход',
        'has_other_loans': 'Наличие других кредитов',
        'other_loans_monthly_payment': 'Платежи по другим кредитам'
    }
    
    @classmethod
    def is_field_protected(cls, personal_data: PersonalData, field_name: str) -> bool:
        """
        Проверяет, защищено ли поле от изменения
        
        Args:
            personal_data: Объект персональных данных
            field_name: Имя поля для проверки
            
        Returns:
            True если поле защищено (заполнено и не редактируемое)
        """
        # Всегда редактируемые поля никогда не защищены
        if field_name in cls.ALWAYS_EDITABLE_FIELDS:
            return False
            
        # Защищенные поля блокируются если заполнены
        if field_name in cls.PROTECTED_FIELDS:
            field_value = getattr(personal_data, field_name, None)
            return field_value is not None
            
        return False
    
    @classmethod
    def get_protected_fields(cls, personal_data: PersonalData) -> List[str]:
        """Возвращает список защищенных полей"""
        protected = []
        for field_name in cls.PROTECTED_FIELDS:
            if cls.is_field_protected(personal_data, field_name):
                protected.append(field_name)
        return protected
    
    @classmethod
    def get_editable_fields(cls, personal_data: PersonalData) -> List[str]:
        """Возвращает список полей доступных для редактирования"""
        editable = []
        
        # Всегда редактируемые поля
        editable.extend(cls.ALWAYS_EDITABLE_FIELDS.keys())
        
        # Незаполненные защищенные поля
        for field_name in cls.PROTECTED_FIELDS:
            if not cls.is_field_protected(personal_data, field_name):
                editable.append(field_name)
                
        return editable
    
    @classmethod
    def get_field_status(cls, personal_data: PersonalData) -> Dict[str, Dict[str, any]]:
        """
        Возвращает статус всех полей
        
        Returns:
            Dict с информацией о каждом поле:
            {
                'field_name': {
                    'is_protected': bool,
                    'is_filled': bool,
                    'display_name': str,
                    'current_value': any
                }
            }
        """
        status = {}
        
        all_fields = {**cls.PROTECTED_FIELDS, **cls.ALWAYS_EDITABLE_FIELDS}
        
        for field_name, display_name in all_fields.items():
            field_value = getattr(personal_data, field_name, None)
            
            status[field_name] = {
                'is_protected': cls.is_field_protected(personal_data, field_name),
                'is_filled': field_value is not None,
                'display_name': display_name,
                'current_value': field_value,
                'is_always_editable': field_name in cls.ALWAYS_EDITABLE_FIELDS
            }
            
        return status
    
    @classmethod
    def get_protection_reason(cls, field_name: str, translate=None) -> str:
        """Возвращает объяснение, почему поле защищено"""
        _ = translate if translate else lambda x: x
        
        if field_name in cls.PROTECTED_FIELDS:
            return _(
                "This field is protected because it's already filled and affects "
                "your credit score. This ensures the reliability of your assessment."
            )
        
        return _("This field is protected.")
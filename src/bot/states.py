from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    """Состояния для онбординга"""
    waiting_for_phone = State()
    waiting_for_language = State()


class LoanApplicationStates(StatesGroup):
    """Состояния для создания заявки на кредит"""
    # Общие состояния
    choosing_loan_type = State()
    entering_amount = State()
    entering_rate = State()
    entering_term = State()
    entering_income = State()
    entering_other_payments = State()
    
    # Для автокредита
    choosing_car_condition = State()
    
    # Для микрозайма
    choosing_receive_method = State()
    
    # Подтверждение
    confirming_application = State()


class PersonalDataStates(StatesGroup):
    """Состояния для сбора персональных данных"""
    entering_age = State()
    choosing_gender = State()
    entering_work_experience = State()
    entering_address_stability = State()
    choosing_housing_status = State()
    choosing_marital_status = State()
    choosing_education = State()
    entering_closed_loans = State()
    choosing_region = State()
    
    # Итоговое состояние
    reviewing_data = State()


class BankFlowStates(StatesGroup):
    """Состояния для отправки в банк"""
    confirming_send = State()
    waiting_response = State()
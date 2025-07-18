from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any, Callable

from src.core.enums import PDNStatus, LoanType


class PDNCalculator:
    """Калькулятор показателя долговой нагрузки (ПДН)"""

    # Лимиты для разных типов кредитов
    LOAN_LIMITS = {
        LoanType.MICROLOAN: {
            "max_amount": 100_000_000,  # 100 млн сум
            "min_rate": 18,  # 18%
            "max_rate": 79,  # 79%
            "min_term_months": 1,
            "max_term_months": 36,  # 3 года
        },
        LoanType.CARLOAN: {
            "max_amount": 1_000_000_000,  # 1 млрд сум
            "min_rate": 4,  # 4%
            "max_rate": 48,  # 48%
            "min_term_months": 6,
            "max_term_months": 60,  # 5 лет
        },
    }

    # Пороговые значения ПДН
    PDN_THRESHOLDS = {
        "warning": 35,  # Предупреждение
        "danger": 50,  # Опасный уровень (банки не выдают кредиты)
    }

    @staticmethod
    def calculate_annuity_payment(
        amount: Decimal, annual_rate: Decimal, term_months: int,
        translate: Optional[Callable[[str], str]] = None
    ) -> Decimal:
        """
        Расчет аннуитетного платежа по формуле:
        A = P × [r(1+r)^n] / [(1+r)^n - 1]
        
        Args:
            amount: Сумма кредита
            annual_rate: Годовая процентная ставка (в процентах)
            term_months: Срок кредита в месяцах
            translate: Функция перевода (опционально)
            
        Returns:
            Ежемесячный аннуитетный платеж
        """
        if amount <= 0 or annual_rate < 0 or term_months <= 0:
            msg = translate('Invalid calculation parameters') if translate else 'Invalid calculation parameters'
            raise ValueError(msg)

        # Если ставка 0%, то просто делим сумму на количество месяцев
        if annual_rate == 0:
            return (amount / term_months).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        # Месячная процентная ставка
        monthly_rate = annual_rate / 12 / 100

        # Расчет аннуитетного коэффициента
        rate_power = (1 + monthly_rate) ** term_months
        annuity_coefficient = (monthly_rate * rate_power) / (rate_power - 1)

        # Расчет платежа
        payment = amount * annuity_coefficient
        return payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_pdn(
        monthly_payment: Decimal,
        monthly_income: Decimal,
        other_payments: Optional[Decimal] = None,
        translate: Optional[Callable[[str], str]] = None
    ) -> Decimal:
        """
        Расчет показателя долговой нагрузки (ПДН)
        
        Args:
            monthly_payment: Ежемесячный платеж по новому кредиту
            monthly_income: Ежемесячный доход
            other_payments: Ежемесячные платежи по другим кредитам
            translate: Функция перевода (опционально)
            
        Returns:
            ПДН в процентах
        """
        if monthly_income <= 0:
            msg = translate('Income must be positive') if translate else 'Income must be positive'
            raise ValueError(msg)

        total_payments = monthly_payment
        if other_payments and other_payments > 0:
            total_payments += other_payments

        pdn = (total_payments / monthly_income) * 100
        return pdn.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def get_pdn_status(pdn_value: Decimal) -> PDNStatus:
        """
        Определение статуса ПДН для визуализации
        
        Args:
            pdn_value: Значение ПДН в процентах
            
        Returns:
            Статус ПДН (зеленый/желтый/красный)
        """
        if pdn_value < PDNCalculator.PDN_THRESHOLDS["warning"]:
            return PDNStatus.GREEN
        elif pdn_value <= PDNCalculator.PDN_THRESHOLDS["danger"]:
            return PDNStatus.YELLOW
        else:
            return PDNStatus.RED

    @staticmethod
    def get_pdn_emoji(status: PDNStatus) -> str:
        """Получение эмодзи для статуса ПДН"""
        return {
            PDNStatus.GREEN: "🟢",
            PDNStatus.YELLOW: "🟡",
            PDNStatus.RED: "🔴",
        }[status]

    @staticmethod
    def validate_loan_parameters(
        loan_type: LoanType, amount: Decimal, rate: Decimal, term_months: int,
        translate: Optional[Callable[[str], str]] = None
    ) -> Dict[str, Any]:
        """
        Валидация параметров кредита
        
        Args:
            loan_type: Тип кредита
            amount: Сумма кредита
            rate: Процентная ставка
            term_months: Срок в месяцах
            translate: Функция перевода (опционально)
            
        Returns:
            Словарь с результатами валидации
        """
        limits = PDNCalculator.LOAN_LIMITS[loan_type]
        errors = []

        if amount <= 0:
            msg = translate('Loan amount must be positive') if translate else 'Loan amount must be positive'
            errors.append(msg)
        elif amount > limits["max_amount"]:
            if translate:
                msg = translate('Amount exceeds maximum for {loan_type}: {max_amount} sum').format(
                    loan_type=loan_type.value, max_amount=f"{limits['max_amount']:,}"
                )
            else:
                msg = f"Amount exceeds maximum for {loan_type.value}: {limits['max_amount']:,} sum"
            errors.append(msg)

        if rate < limits["min_rate"] or rate > limits["max_rate"]:
            if translate:
                msg = translate('Rate must be between {min_rate}% and {max_rate}%').format(
                    min_rate=limits['min_rate'], max_rate=limits['max_rate']
                )
            else:
                msg = f"Rate must be between {limits['min_rate']}% and {limits['max_rate']}%"
            errors.append(msg)

        if (
            term_months < limits["min_term_months"]
            or term_months > limits["max_term_months"]
        ):
            if translate:
                msg = translate('Term must be from {min_term} to {max_term} months').format(
                    min_term=limits['min_term_months'], max_term=limits['max_term_months']
                )
            else:
                msg = f"Term must be from {limits['min_term_months']} to {limits['max_term_months']} months"
            errors.append(msg)

        return {"valid": len(errors) == 0, "errors": errors}

    @staticmethod
    def can_get_loan(pdn_value: Decimal) -> bool:
        """
        Проверка возможности получения кредита по ПДН
        
        В Узбекистане банки не могут выдавать кредиты при ПДН > 50%
        """
        return pdn_value <= PDNCalculator.PDN_THRESHOLDS["danger"]

    @staticmethod
    def format_amount(amount: Decimal) -> str:
        """Форматирование суммы для отображения"""
        return f"{amount:,.0f}".replace(",", " ")

    @staticmethod
    def get_pdn_description(pdn_value: Decimal, status: PDNStatus, translate=None) -> str:
        """Получение описания ПДН для пользователя"""
        _ = translate if translate else lambda x: x
        emoji = PDNCalculator.get_pdn_emoji(status)
        
        if status == PDNStatus.GREEN:
            desc = _("Excellent indicator! Banks will readily approve the loan.")
        elif status == PDNStatus.YELLOW:
            desc = _("Acceptable indicator. Loan approval is possible.")
        else:
            desc = _("High debt burden! Banks won't be able to issue a loan.")
            
        return f"{emoji} {_('DTI')}: {pdn_value}%\\n{desc}"
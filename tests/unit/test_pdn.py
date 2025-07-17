import pytest
from decimal import Decimal

from src.core.enums import LoanType, PDNStatus
from src.core.pdn import PDNCalculator


class TestPDNCalculator:
    """Тесты для калькулятора ПДН"""

    def test_calculate_annuity_payment_basic(self):
        """Тест базового расчета аннуитетного платежа"""
        # 1 млн сум, 20% годовых, 12 месяцев
        amount = Decimal("1000000")
        rate = Decimal("20")
        term = 12
        
        payment = PDNCalculator.calculate_annuity_payment(amount, rate, term)
        
        # Ожидаемый платеж около 92,634 сум
        assert payment == Decimal("92634.47")

    def test_calculate_annuity_payment_zero_rate(self):
        """Тест расчета при нулевой ставке"""
        amount = Decimal("1000000")
        rate = Decimal("0")
        term = 10
        
        payment = PDNCalculator.calculate_annuity_payment(amount, rate, term)
        
        # При 0% просто делим сумму на срок
        assert payment == Decimal("100000.00")

    def test_calculate_annuity_payment_invalid_params(self):
        """Тест с некорректными параметрами"""
        with pytest.raises(ValueError):
            PDNCalculator.calculate_annuity_payment(
                Decimal("-1000"), Decimal("10"), 12
            )
        
        with pytest.raises(ValueError):
            PDNCalculator.calculate_annuity_payment(
                Decimal("1000"), Decimal("-5"), 12
            )
        
        with pytest.raises(ValueError):
            PDNCalculator.calculate_annuity_payment(
                Decimal("1000"), Decimal("10"), 0
            )

    def test_calculate_pdn_basic(self):
        """Тест базового расчета ПДН"""
        monthly_payment = Decimal("50000")
        monthly_income = Decimal("200000")
        
        pdn = PDNCalculator.calculate_pdn(monthly_payment, monthly_income)
        
        assert pdn == Decimal("25.00")

    def test_calculate_pdn_with_other_payments(self):
        """Тест расчета ПДН с другими платежами"""
        monthly_payment = Decimal("50000")
        monthly_income = Decimal("200000")
        other_payments = Decimal("30000")
        
        pdn = PDNCalculator.calculate_pdn(
            monthly_payment, monthly_income, other_payments
        )
        
        # (50000 + 30000) / 200000 * 100 = 40%
        assert pdn == Decimal("40.00")

    def test_calculate_pdn_invalid_income(self):
        """Тест с некорректным доходом"""
        with pytest.raises(ValueError):
            PDNCalculator.calculate_pdn(
                Decimal("50000"), Decimal("0")
            )
        
        with pytest.raises(ValueError):
            PDNCalculator.calculate_pdn(
                Decimal("50000"), Decimal("-100000")
            )

    def test_get_pdn_status(self):
        """Тест определения статуса ПДН"""
        assert PDNCalculator.get_pdn_status(Decimal("20")) == PDNStatus.GREEN
        assert PDNCalculator.get_pdn_status(Decimal("34.99")) == PDNStatus.GREEN
        assert PDNCalculator.get_pdn_status(Decimal("35")) == PDNStatus.YELLOW
        assert PDNCalculator.get_pdn_status(Decimal("45")) == PDNStatus.YELLOW
        assert PDNCalculator.get_pdn_status(Decimal("50")) == PDNStatus.YELLOW
        assert PDNCalculator.get_pdn_status(Decimal("50.01")) == PDNStatus.RED
        assert PDNCalculator.get_pdn_status(Decimal("75")) == PDNStatus.RED

    def test_get_pdn_emoji(self):
        """Тест получения эмодзи для статуса"""
        assert PDNCalculator.get_pdn_emoji(PDNStatus.GREEN) == "🟢"
        assert PDNCalculator.get_pdn_emoji(PDNStatus.YELLOW) == "🟡"
        assert PDNCalculator.get_pdn_emoji(PDNStatus.RED) == "🔴"

    def test_validate_loan_parameters_microloan(self):
        """Тест валидации параметров микрозайма"""
        # Валидные параметры
        result = PDNCalculator.validate_loan_parameters(
            LoanType.MICROLOAN,
            Decimal("5000000"),  # 5 млн
            Decimal("25"),       # 25%
            24                   # 2 года
        )
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        
        # Сумма превышает лимит
        result = PDNCalculator.validate_loan_parameters(
            LoanType.MICROLOAN,
            Decimal("200000000"),  # 200 млн
            Decimal("25"),
            24
        )
        assert result["valid"] is False
        assert any("превышает максимальную" in e for e in result["errors"])
        
        # Ставка вне диапазона
        result = PDNCalculator.validate_loan_parameters(
            LoanType.MICROLOAN,
            Decimal("5000000"),
            Decimal("10"),  # Меньше 18%
            24
        )
        assert result["valid"] is False
        assert any("Ставка должна быть" in e for e in result["errors"])

    def test_validate_loan_parameters_carloan(self):
        """Тест валидации параметров автокредита"""
        # Валидные параметры
        result = PDNCalculator.validate_loan_parameters(
            LoanType.CARLOAN,
            Decimal("500000000"),  # 500 млн
            Decimal("15"),         # 15%
            36                     # 3 года
        )
        assert result["valid"] is True
        
        # Срок вне диапазона
        result = PDNCalculator.validate_loan_parameters(
            LoanType.CARLOAN,
            Decimal("500000000"),
            Decimal("15"),
            3  # 3 месяца - меньше минимума
        )
        assert result["valid"] is False
        assert any("Срок должен быть" in e for e in result["errors"])

    def test_can_get_loan(self):
        """Тест проверки возможности получения кредита"""
        assert PDNCalculator.can_get_loan(Decimal("30")) is True
        assert PDNCalculator.can_get_loan(Decimal("50")) is True
        assert PDNCalculator.can_get_loan(Decimal("50.01")) is False
        assert PDNCalculator.can_get_loan(Decimal("75")) is False

    def test_format_amount(self):
        """Тест форматирования суммы"""
        assert PDNCalculator.format_amount(Decimal("1000000")) == "1 000 000"
        assert PDNCalculator.format_amount(Decimal("1234567.89")) == "1 234 568"
        assert PDNCalculator.format_amount(Decimal("100")) == "100"

    def test_get_pdn_description(self):
        """Тест получения описания ПДН"""
        desc = PDNCalculator.get_pdn_description(
            Decimal("25"), PDNStatus.GREEN
        )
        assert "🟢" in desc
        assert "25%" in desc
        assert "Отличный показатель" in desc
        
        desc = PDNCalculator.get_pdn_description(
            Decimal("55"), PDNStatus.RED
        )
        assert "🔴" in desc
        assert "55%" in desc
        assert "не смогут выдать кредит" in desc
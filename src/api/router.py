from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import LoanStatus, LoanType
from src.core.pdn import PDNCalculator
from src.core.scoring import PersonalData, ScoringCalculator
from src.db.database import get_db
from src.db.models import LoanApplication, PersonalData as PersonalDataModel, User

router = APIRouter()


# Pydantic модели для API
class PDNCalculationRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Сумма кредита")
    annual_rate: Decimal = Field(..., ge=0, le=100, description="Годовая ставка в процентах")
    term_months: int = Field(..., gt=0, description="Срок кредита в месяцах")
    monthly_income: Decimal = Field(..., gt=0, description="Ежемесячный доход")
    other_payments: Optional[Decimal] = Field(0, ge=0, description="Другие ежемесячные платежи")


class PDNCalculationResponse(BaseModel):
    monthly_payment: Decimal
    pdn_value: Decimal
    pdn_status: str
    can_get_loan: bool
    description: str


class ScoringRequest(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    work_experience_months: Optional[int] = None
    address_stability_years: Optional[int] = None
    housing_status: Optional[str] = None
    marital_status: Optional[str] = None
    education: Optional[str] = None
    closed_loans_count: Optional[int] = None
    has_other_loans: bool = False
    pdn_with_other_loans: Optional[Decimal] = None
    region: Optional[str] = None
    device_type: Optional[str] = None
    referral_count: int = 0


class ScoringResponse(BaseModel):
    score: int
    level: str
    breakdown: dict


class LoanApplicationResponse(BaseModel):
    id: int
    loan_type: LoanType
    amount: Decimal
    annual_rate: Decimal
    term_months: int
    monthly_payment: Decimal
    pdn_value: Decimal
    status: LoanStatus
    created_at: datetime


@router.post("/calculate/pdn", response_model=PDNCalculationResponse)
async def calculate_pdn(request: PDNCalculationRequest):
    """Расчет показателя долговой нагрузки"""
    try:
        # Расчет аннуитетного платежа
        monthly_payment = PDNCalculator.calculate_annuity_payment(
            request.amount,
            request.annual_rate,
            request.term_months
        )
        
        # Расчет ПДН
        pdn_value = PDNCalculator.calculate_pdn(
            monthly_payment,
            request.monthly_income,
            request.other_payments
        )
        
        # Получение статуса
        pdn_status = PDNCalculator.get_pdn_status(pdn_value)
        
        # Проверка возможности получения кредита
        can_get_loan = PDNCalculator.can_get_loan(pdn_value)
        
        # Описание
        description = PDNCalculator.get_pdn_description(pdn_value, pdn_status)
        
        return PDNCalculationResponse(
            monthly_payment=monthly_payment,
            pdn_value=pdn_value,
            pdn_status=pdn_status.value,
            can_get_loan=can_get_loan,
            description=description
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calculate/scoring", response_model=ScoringResponse)
async def calculate_scoring(request: ScoringRequest):
    """Расчет скоринг-балла"""
    try:
        # Создаем объект персональных данных
        personal_data = PersonalData(**request.dict())
        
        # Расчет скоринга
        score = ScoringCalculator.calculate_score(personal_data)
        
        # Получение уровня
        level = ScoringCalculator.get_score_level(score)
        
        # Детализация
        breakdown = ScoringCalculator.get_score_breakdown(personal_data)
        
        return ScoringResponse(
            score=score,
            level=level,
            breakdown=breakdown
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{telegram_id}/applications", response_model=List[LoanApplicationResponse])
async def get_user_applications(
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
    include_archived: bool = False
):
    """Получение заявок пользователя"""
    # Находим пользователя
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем заявки
    query = select(LoanApplication).where(LoanApplication.user_id == user.id)
    
    if not include_archived:
        query = query.where(LoanApplication.is_archived == False)
    
    query = query.order_by(LoanApplication.created_at.desc())
    
    result = await db.execute(query)
    applications = result.scalars().all()
    
    return [
        LoanApplicationResponse(
            id=app.id,
            loan_type=app.loan_type,
            amount=app.amount,
            annual_rate=app.annual_rate,
            term_months=app.term_months,
            monthly_payment=app.monthly_payment,
            pdn_value=app.pdn_value,
            status=app.status,
            created_at=app.created_at
        )
        for app in applications
    ]


@router.get("/webhook/{webhook_secret}", include_in_schema=False)
async def telegram_webhook(webhook_secret: str):
    """Эндпоинт для Telegram webhook"""
    # Этот эндпоинт будет использоваться ботом
    return {"status": "ok"}
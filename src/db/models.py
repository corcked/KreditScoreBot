from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from src.core.enums import (
    CarCondition,
    DeviceType,
    Education,
    Gender,
    HousingStatus,
    LoanStatus,
    LoanType,
    MaritalStatus,
    ReceiveMethod,
    Region,
)

Base = declarative_base()


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    language_code = Column(String(10), default="ru")
    
    # Реферальная система
    referral_code = Column(String(20), unique=True, nullable=False)
    referred_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    referral_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    loan_applications = relationship("LoanApplication", back_populates="user")
    personal_data = relationship("PersonalData", back_populates="user", uselist=False)
    referrals = relationship("User", backref="referrer", remote_side=[id])
    referral_registrations = relationship("ReferralRegistration", back_populates="referrer", foreign_keys="ReferralRegistration.referrer_id")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"


class PersonalData(Base):
    """Персональные данные пользователя для скоринга"""
    __tablename__ = "personal_data"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Основные данные
    age = Column(Integer, nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    region = Column(Enum(Region), nullable=True)
    device_type = Column(Enum(DeviceType), nullable=True)
    
    # Работа и доход
    monthly_income = Column(Numeric(15, 2), nullable=True)
    work_experience_months = Column(Integer, nullable=True)
    
    # Жилье и семья
    address_stability_years = Column(Integer, nullable=True)
    housing_status = Column(Enum(HousingStatus), nullable=True)
    marital_status = Column(Enum(MaritalStatus), nullable=True)
    
    # Образование и кредитная история
    education = Column(Enum(Education), nullable=True)
    closed_loans_count = Column(Integer, default=0)
    has_other_loans = Column(Boolean, default=False)
    other_loans_monthly_payment = Column(Numeric(15, 2), nullable=True)
    
    # Скоринг
    current_score = Column(Integer, default=0)
    score_updated_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="personal_data")
    
    def __repr__(self):
        return f"<PersonalData(user_id={self.user_id}, score={self.current_score})>"


class LoanApplication(Base):
    """Заявка на кредит"""
    __tablename__ = "loan_applications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Тип и параметры кредита
    loan_type = Column(Enum(LoanType), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    annual_rate = Column(Numeric(5, 2), nullable=False)
    term_months = Column(Integer, nullable=False)
    
    # Дополнительные параметры
    car_condition = Column(Enum(CarCondition), nullable=True)  # Для автокредита
    receive_method = Column(Enum(ReceiveMethod), nullable=True)  # Для микрозайма
    
    # Расчетные показатели
    monthly_payment = Column(Numeric(15, 2), nullable=False)
    pdn_value = Column(Numeric(5, 2), nullable=False)
    
    # Статус
    status = Column(Enum(LoanStatus), default=LoanStatus.NEW, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # Отправка в банк
    sent_to_bank_at = Column(DateTime, nullable=True)
    bank_response_at = Column(DateTime, nullable=True)
    bank_response = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="loan_applications")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_user_archived", "user_id", "is_archived"),
    )
    
    def __repr__(self):
        return f"<LoanApplication(id={self.id}, user_id={self.user_id}, type={self.loan_type}, status={self.status})>"


class ReferralRegistration(Base):
    """Регистрации по реферальным ссылкам"""
    __tablename__ = "referral_registrations"

    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referred_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Бонусы
    bonus_points = Column(Integer, default=20)
    bonus_applied = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    referrer = relationship("User", back_populates="referral_registrations", foreign_keys=[referrer_id])
    referred_user = relationship("User", foreign_keys=[referred_user_id])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("referred_user_id", name="uq_referred_user"),
        Index("idx_referrer_created", "referrer_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<ReferralRegistration(referrer={self.referrer_id}, referred={self.referred_user_id})>"


class BotState(Base):
    """Состояние FSM бота для пользователя"""
    __tablename__ = "bot_states"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # FSM состояние
    state = Column(String(100), nullable=True)
    state_data = Column(Text, nullable=True)  # JSON
    
    # Текущая заявка в процессе создания
    current_application_data = Column(Text, nullable=True)  # JSON
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<BotState(user_id={self.user_id}, state={self.state})>"
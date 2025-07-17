from enum import Enum


class LoanType(str, Enum):
    MICROLOAN = "microloan"
    CARLOAN = "carloan"


class LoanStatus(str, Enum):
    NEW = "new"
    SENT = "sent"
    ARCHIVED = "archived"


class CarCondition(str, Enum):
    NEW = "new"
    USED = "used"


class ReceiveMethod(str, Enum):
    CARD = "card"
    CASH = "cash"


class PDNStatus(str, Enum):
    GREEN = "green"  # <35%
    YELLOW = "yellow"  # 35-50%
    RED = "red"  # >50%


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class MaritalStatus(str, Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"


class Education(str, Enum):
    SECONDARY = "secondary"
    VOCATIONAL = "vocational"
    INCOMPLETE_HIGHER = "incomplete_higher"
    HIGHER = "higher"
    POSTGRADUATE = "postgraduate"


class HousingStatus(str, Enum):
    OWN = "own"
    OWN_WITH_MORTGAGE = "own_with_mortgage"
    RENT = "rent"
    RELATIVES = "relatives"


class Region(str, Enum):
    TASHKENT = "tashkent"
    TASHKENT_REGION = "tashkent_region"
    ANDIJAN = "andijan"
    BUKHARA = "bukhara"
    FERGANA = "fergana"
    JIZZAKH = "jizzakh"
    NAMANGAN = "namangan"
    NAVOIY = "navoiy"
    QASHQADARYO = "qashqadaryo"
    SAMARKAND = "samarkand"
    SIRDARYO = "sirdaryo"
    SURXONDARYO = "surxondaryo"
    XORAZM = "xorazm"
    KARAKALPAKSTAN = "karakalpakstan"


class DeviceType(str, Enum):
    APPLE = "apple"
    ANDROID = "android"
    OTHER = "other"
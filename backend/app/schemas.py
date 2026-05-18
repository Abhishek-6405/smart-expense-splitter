from pydantic import BaseModel, EmailStr, validator, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

# --- Enums ---
class SplitMode(str, Enum):
    equal = "equal"
    subset = "subset"
    custom = "custom"
    weighted = "weighted"

# -------------------
# USER SCHEMAS
# -------------------

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    avatar_color: Optional[str] = "#6366f1"

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    avatar_color: str
    created_at: datetime

    class Config:
        from_attributes = True

# -------------------
# GROUP SCHEMAS
# -------------------

class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    currency: Optional[str] = "INR"
    created_by: str
    member_ids: List[str] = Field(..., min_items=1)

class GroupOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    currency: str
    created_at: datetime
    created_by: str
    members: List[UserOut] = []

    class Config:
        from_attributes = True

class AddMemberRequest(BaseModel):
    user_id: str

# -------------------
# EXPENSE SCHEMAS
# -------------------

class ExpenseShareInput(BaseModel):
    user_id: str
    share_paise: int = Field(..., gt=0)

class ExpenseCreate(BaseModel):
    paid_by: str
    amount_paise: int = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=500)
    date: datetime
    split_mode: SplitMode
    shares: List[ExpenseShareInput]

    @validator("shares")
    def shares_must_sum_to_total(cls, shares, values):
        if "amount_paise" in values:
            total = sum(s.share_paise for s in shares)
            if total != values["amount_paise"]:
                raise ValueError(
                    f"Shares sum to {total} paise but expense total is {values['amount_paise']} paise. They must match exactly."
                )
        return shares

    @validator("shares")
    def must_have_at_least_one_share(cls, shares):
        if len(shares) == 0:
            raise ValueError("Expense must have at least one share")
        return shares

class ExpenseShareOut(BaseModel):
    id: str
    user_id: str
    share_paise: int
    user: UserOut

    class Config:
        from_attributes = True

class ExpenseOut(BaseModel):
    id: str
    group_id: str
    paid_by: str
    amount_paise: int
    description: str
    date: datetime
    split_mode: str
    created_at: datetime
    paid_by_user: UserOut
    shares: List[ExpenseShareOut]

    class Config:
        from_attributes = True

# -------------------
# BALANCE SCHEMAS
# -------------------

class UserBalance(BaseModel):
    user_id: str
    user_name: str
    avatar_color: str
    net_balance_paise: int

class SettleUpTransaction(BaseModel):
    from_user_id: str
    from_user_name: str
    to_user_id: str
    to_user_name: str
    amount_paise: int

# -------------------
# SETTLEMENT SCHEMAS
# -------------------

class SettlementCreate(BaseModel):
    from_user: str
    to_user: str
    amount_paise: int = Field(..., gt=0)
    note: Optional[str] = None

class SettlementOut(BaseModel):
    id: str
    group_id: str
    from_user: str
    to_user: str
    amount_paise: int
    note: Optional[str]
    date: datetime

    class Config:
        from_attributes = True

# -------------------
# AI SCHEMAS
# -------------------

class AIParseRequest(BaseModel):
    text: str = Field(..., min_length=1)
    group_id: str
    current_user_id: str

class AIShareResult(BaseModel):
    user_id: str
    user_name: str
    share_paise: int

class AIParseResult(BaseModel):
    success: bool
    confidence: float
    payer_id: Optional[str] = None
    payer_name: Optional[str] = None
    amount_paise: Optional[int] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    split_mode: Optional[str] = None
    shares: Optional[List[AIShareResult]] = None
    raw_text: Optional[str] = None
    error: Optional[str] = None
    fallback: bool = False

class BillParseRequest(BaseModel):
    bill_text: str = Field(..., min_length=1)
    group_id: str

class BillItem(BaseModel):
    item_name: str
    amount_paise: int
    quantity: int = 1

class BillParseResult(BaseModel):
    success: bool
    items: Optional[List[BillItem]] = None
    subtotal_paise: Optional[int] = None
    tax_paise: Optional[int] = None
    total_paise: Optional[int] = None
    error: Optional[str] = None
    fallback: bool = False
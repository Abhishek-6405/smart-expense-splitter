 
from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey, DateTime, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

# --- Enums ---
class SplitMode(str, enum.Enum):
    equal = "equal"
    subset = "subset"
    custom = "custom"
    weighted = "weighted"

class Currency(str, enum.Enum):
    INR = "INR"
    USD = "USD"
    EUR = "EUR"

# --- Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=False, unique=True)
    avatar_color = Column(String(20), default="#6366f1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    group_memberships = relationship("GroupMember", back_populates="user")
    expenses_paid = relationship("Expense", back_populates="paid_by_user")
    expense_shares = relationship("ExpenseShare", back_populates="user")


class Group(Base):
    __tablename__ = "groups"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    currency = Column(String(10), default="INR")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    is_deleted = Column(Boolean, default=False)

    members = relationship("GroupMember", back_populates="group")
    expenses = relationship("Expense", back_populates="group")


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(String, primary_key=True, default=generate_uuid)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String, primary_key=True, default=generate_uuid)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    paid_by = Column(String, ForeignKey("users.id"), nullable=False)
    amount_paise = Column(BigInteger, nullable=False)
    description = Column(String(500), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    split_mode = Column(Enum(SplitMode), nullable=False, default=SplitMode.equal)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_deleted = Column(Boolean, default=False)

    group = relationship("Group", back_populates="expenses")
    paid_by_user = relationship("User", back_populates="expenses_paid")
    shares = relationship("ExpenseShare", back_populates="expense", cascade="all, delete-orphan")


class ExpenseShare(Base):
    __tablename__ = "expense_shares"

    id = Column(String, primary_key=True, default=generate_uuid)
    expense_id = Column(String, ForeignKey("expenses.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    share_paise = Column(BigInteger, nullable=False)

    expense = relationship("Expense", back_populates="shares")
    user = relationship("User", back_populates="expense_shares")


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(String, primary_key=True, default=generate_uuid)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    from_user = Column(String, ForeignKey("users.id"), nullable=False)
    to_user = Column(String, ForeignKey("users.id"), nullable=False)
    amount_paise = Column(BigInteger, nullable=False)
    note = Column(String(500), nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
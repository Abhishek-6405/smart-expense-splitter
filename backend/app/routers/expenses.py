from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import Expense, ExpenseShare, GroupMember, User, Group
from ..schemas import ExpenseCreate, ExpenseOut

router = APIRouter()

@router.post("/{group_id}/expenses", response_model=ExpenseOut, status_code=201)
def create_expense(
    group_id: str,
    expense: ExpenseCreate,
    db: Session = Depends(get_db)
):
    # Check group exists
    group = db.query(Group).filter(
        Group.id == group_id,
        Group.is_deleted == False
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check payer is a member of the group
    payer_membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == expense.paid_by
    ).first()
    if not payer_membership:
        raise HTTPException(status_code=400, detail="Payer is not a member of this group")

    # Check all share users are members of the group
    member_ids = {gm.user_id for gm in db.query(GroupMember).filter(
        GroupMember.group_id == group_id
    ).all()}

    for share in expense.shares:
        if share.user_id not in member_ids:
            raise HTTPException(
                status_code=400,
                detail=f"User {share.user_id} is not a member of this group"
            )

    # Validate shares sum (double check beyond Pydantic)
    total_shares = sum(s.share_paise for s in expense.shares)
    if total_shares != expense.amount_paise:
        raise HTTPException(
            status_code=400,
            detail=f"Shares sum ({total_shares} paise) must equal expense amount ({expense.amount_paise} paise)"
        )

    # Create expense
    new_expense = Expense(
        group_id=group_id,
        paid_by=expense.paid_by,
        amount_paise=expense.amount_paise,
        description=expense.description,
        date=expense.date,
        split_mode=expense.split_mode
    )
    db.add(new_expense)
    db.flush()

    # Create shares
    for share in expense.shares:
        new_share = ExpenseShare(
            expense_id=new_expense.id,
            user_id=share.user_id,
            share_paise=share.share_paise
        )
        db.add(new_share)

    db.commit()
    db.refresh(new_expense)
    return new_expense

@router.get("/{group_id}/expenses", response_model=List[ExpenseOut])
def get_expenses(
    group_id: str,
    paid_by: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    # Check group exists
    group = db.query(Group).filter(
        Group.id == group_id,
        Group.is_deleted == False
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Base query
    query = db.query(Expense).filter(
        Expense.group_id == group_id,
        Expense.is_deleted == False
    )

    # Apply filters
    if paid_by:
        query = query.filter(Expense.paid_by == paid_by)

    if date_from:
        query = query.filter(Expense.date >= date_from)

    if date_to:
        query = query.filter(Expense.date <= date_to)

    if search:
        query = query.filter(
            Expense.description.ilike(f"%{search}%")
        )

    expenses = query.order_by(Expense.date.desc()).all()
    return expenses

@router.get("/{group_id}/expenses/{expense_id}", response_model=ExpenseOut)
def get_expense(
    group_id: str,
    expense_id: str,
    db: Session = Depends(get_db)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.group_id == group_id,
        Expense.is_deleted == False
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

@router.delete("/{group_id}/expenses/{expense_id}", status_code=204)
def delete_expense(
    group_id: str,
    expense_id: str,
    db: Session = Depends(get_db)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.group_id == group_id,
        Expense.is_deleted == False
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    expense.is_deleted = True
    db.commit()
    return 

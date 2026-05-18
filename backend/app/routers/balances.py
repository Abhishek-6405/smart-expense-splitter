from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Expense, ExpenseShare, GroupMember, User, Group, Settlement
from ..schemas import UserBalance, SettleUpTransaction, SettlementCreate, SettlementOut

router = APIRouter()

def calculate_balances(group_id: str, db: Session):
    """
    Calculate net balance for each member in a group.
    Positive = they are owed money
    Negative = they owe money
    """
    # Get all group members
    memberships = db.query(GroupMember).filter(
        GroupMember.group_id == group_id
    ).all()

    # Initialize balance dict for every member
    balances = {}
    for gm in memberships:
        balances[gm.user_id] = 0

    # Add what each person paid
    expenses = db.query(Expense).filter(
        Expense.group_id == group_id,
        Expense.is_deleted == False
    ).all()

    for expense in expenses:
        balances[expense.paid_by] += expense.amount_paise

    # Subtract what each person owes (their shares)
    shares = db.query(ExpenseShare).join(Expense).filter(
        Expense.group_id == group_id,
        Expense.is_deleted == False
    ).all()

    for share in shares:
        balances[share.user_id] -= share.share_paise

    # Apply settlements
    settlements = db.query(Settlement).filter(
        Settlement.group_id == group_id
    ).all()

    for settlement in settlements:
        balances[settlement.from_user] += settlement.amount_paise
        balances[settlement.to_user] -= settlement.amount_paise

    return balances

def settle_up_algorithm(balances: dict, db: Session):
    """
    Greedy algorithm to minimize number of transactions.

    Steps:
    1. Separate into creditors (positive balance) and debtors (negative balance)
    2. Sort both lists by absolute value descending
    3. Match largest debtor with largest creditor
    4. Settle minimum of the two amounts
    5. Move pointer for whoever is fully settled
    6. Repeat until all balances are zero

    This greedy approach guarantees minimum number of transactions.
    Time complexity: O(n log n)
    """
    # Build creditors and debtors lists
    # creditors = people who are owed money (positive balance)
    # debtors = people who owe money (negative balance)
    creditors = []
    debtors = []

    for user_id, balance in balances.items():
        if balance > 0:
            creditors.append([user_id, balance])
        elif balance < 0:
            debtors.append([user_id, abs(balance)])

    # Sort both by amount descending
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)

    transactions = []
    i = 0  # pointer for debtors
    j = 0  # pointer for creditors

    while i < len(debtors) and j < len(creditors):
        debtor_id, debt_amount = debtors[i]
        creditor_id, credit_amount = creditors[j]

        # Settle the minimum of the two
        settle_amount = min(debt_amount, credit_amount)

        transactions.append({
            "from_user_id": debtor_id,
            "to_user_id": creditor_id,
            "amount_paise": settle_amount
        })

        # Reduce both balances
        debtors[i][1] -= settle_amount
        creditors[j][1] -= settle_amount

        # Move pointer if fully settled
        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1

    return transactions

@router.get("/{group_id}/balances", response_model=List[UserBalance])
def get_balances(group_id: str, db: Session = Depends(get_db)):
    # Check group exists
    group = db.query(Group).filter(
        Group.id == group_id,
        Group.is_deleted == False
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    balances = calculate_balances(group_id, db)

    result = []
    for user_id, net_balance in balances.items():
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            result.append(UserBalance(
                user_id=user_id,
                user_name=user.name,
                avatar_color=user.avatar_color,
                net_balance_paise=net_balance
            ))

    return result

@router.get("/{group_id}/settle-up", response_model=List[SettleUpTransaction])
def get_settle_up(group_id: str, db: Session = Depends(get_db)):
    # Check group exists
    group = db.query(Group).filter(
        Group.id == group_id,
        Group.is_deleted == False
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    balances = calculate_balances(group_id, db)
    transactions = settle_up_algorithm(balances, db)

    result = []
    for txn in transactions:
        from_user = db.query(User).filter(User.id == txn["from_user_id"]).first()
        to_user = db.query(User).filter(User.id == txn["to_user_id"]).first()

        if from_user and to_user:
            result.append(SettleUpTransaction(
                from_user_id=txn["from_user_id"],
                from_user_name=from_user.name,
                to_user_id=txn["to_user_id"],
                to_user_name=to_user.name,
                amount_paise=txn["amount_paise"]
            ))

    return result

@router.post("/{group_id}/settlements", response_model=SettlementOut, status_code=201)
def create_settlement(
    group_id: str,
    settlement: SettlementCreate,
    db: Session = Depends(get_db)
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    new_settlement = Settlement(
        group_id=group_id,
        from_user=settlement.from_user,
        to_user=settlement.to_user,
        amount_paise=settlement.amount_paise,
        note=settlement.note
    )
    db.add(new_settlement)
    db.commit()
    db.refresh(new_settlement)
    return new_settlement 

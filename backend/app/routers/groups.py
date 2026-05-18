from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Group, GroupMember, User
from ..schemas import GroupCreate, GroupOut, AddMemberRequest, UserOut

router = APIRouter()

@router.get("/", response_model=List[GroupOut])
def get_all_groups(db: Session = Depends(get_db)):
    groups = db.query(Group).filter(Group.is_deleted == False).all()
    result = []
    for group in groups:
        members = [gm.user for gm in group.members]
        group_data = GroupOut(
            id=group.id,
            name=group.name,
            description=group.description,
            currency=group.currency,
            created_at=group.created_at,
            created_by=group.created_by,
            members=[UserOut.from_orm(m) for m in members]
        )
        result.append(group_data)
    return result

@router.post("/", response_model=GroupOut, status_code=201)
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    # Check creator exists
    creator = db.query(User).filter(User.id == group.created_by).first()
    if not creator:
        raise HTTPException(status_code=404, detail="Creator user not found")

    # Check all member IDs exist
    for uid in group.member_ids:
        user = db.query(User).filter(User.id == uid).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {uid} not found")

    # Create group
    new_group = Group(
        name=group.name,
        description=group.description,
        currency=group.currency,
        created_by=group.created_by
    )
    db.add(new_group)
    db.flush()

    # Add members
    for uid in group.member_ids:
        member = GroupMember(group_id=new_group.id, user_id=uid)
        db.add(member)

    db.commit()
    db.refresh(new_group)

    members = [gm.user for gm in new_group.members]
    return GroupOut(
        id=new_group.id,
        name=new_group.name,
        description=new_group.description,
        currency=new_group.currency,
        created_at=new_group.created_at,
        created_by=new_group.created_by,
        members=[UserOut.from_orm(m) for m in members]
    )

@router.get("/{group_id}", response_model=GroupOut)
def get_group(group_id: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(
        Group.id == group_id,
        Group.is_deleted == False
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    members = [gm.user for gm in group.members]
    return GroupOut(
        id=group.id,
        name=group.name,
        description=group.description,
        currency=group.currency,
        created_at=group.created_at,
        created_by=group.created_by,
        members=[UserOut.from_orm(m) for m in members]
    )

@router.post("/{group_id}/members", response_model=UserOut, status_code=201)
def add_member(group_id: str, request: AddMemberRequest, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check already a member
    existing = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == request.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    new_member = GroupMember(group_id=group_id, user_id=request.user_id)
    db.add(new_member)
    db.commit()
    return user

@router.delete("/{group_id}/members/{user_id}", status_code=204)
def remove_member(group_id: str, user_id: str, db: Session = Depends(get_db)):
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    db.delete(membership)
    db.commit()
    return

@router.delete("/{group_id}", status_code=204)
def delete_group(group_id: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group.is_deleted = True
    db.commit()
    return 

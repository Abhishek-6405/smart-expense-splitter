from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json
import os
from anthropic import Anthropic
from ..database import get_db
from ..models import Group, GroupMember, User
from ..schemas import (
    AIParseRequest, AIParseResult, AIShareResult,
    BillParseRequest, BillParseResult, BillItem
)

router = APIRouter()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_group_members(group_id: str, db: Session):
    """Helper to get all members of a group"""
    memberships = db.query(GroupMember).filter(
        GroupMember.group_id == group_id
    ).all()
    members = []
    for gm in memberships:
        user = db.query(User).filter(User.id == gm.user_id).first()
        if user:
            members.append({"id": user.id, "name": user.name})
    return members

def find_user_by_name(name: str, members: List[dict]):
    """Fuzzy match a name to a group member"""
    name_lower = name.lower().strip()
    # Exact match first
    for member in members:
        if member["name"].lower() == name_lower:
            return member
    # Partial match
    for member in members:
        if name_lower in member["name"].lower() or member["name"].lower() in name_lower:
            return member
    return None

@router.post("/parse-expense", response_model=AIParseResult)
def parse_expense_text(request: AIParseRequest, db: Session = Depends(get_db)):
    # Check group exists
    group = db.query(Group).filter(Group.id == request.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Get group members
    members = get_group_members(request.group_id, db)
    if not members:
        raise HTTPException(status_code=400, detail="Group has no members")

    # Get current user name
    current_user = db.query(User).filter(User.id == request.current_user_id).first()
    current_user_name = current_user.name if current_user else "Unknown"

    member_list_str = ", ".join([m["name"] for m in members])
    today = datetime.now().strftime("%Y-%m-%d")

    # Build the prompt
    system_prompt = f"""You are an expense parsing assistant for a bill splitting app.
Your job is to extract structured expense information from natural language text.

Group members are: {member_list_str}
The person currently logged in is: {current_user_name}
Today's date is: {today}
Default currency: INR (Indian Rupees)

You must respond with ONLY a valid JSON object. No explanation, no markdown, no extra text.
The JSON must match this exact schema:
{{
    "success": true,
    "confidence": 0.95,
    "payer_name": "Aman",
    "amount_paise": 240000,
    "description": "Dinner at restaurant",
    "date": "2025-01-15T20:00:00",
    "split_mode": "custom",
    "shares": [
        {{"name": "Aman", "share_paise": 100000}},
        {{"name": "Priya", "share_paise": 140000}}
    ]
}}

Rules:
- amount_paise = amount in rupees multiplied by 100 (so ₹24 = 2400 paise)
- shares must sum exactly to amount_paise
- split_mode is one of: equal, subset, custom, weighted
- confidence is between 0 and 1 (how sure you are about the parsing)
- If you cannot parse the text reliably, return {{"success": false, "confidence": 0, "error": "reason"}}
- Only use names from the group members list
- If "me" or "I" is used, it refers to {current_user_name}
- date should be ISO format, use today if not specified"""

    user_prompt = f"Parse this expense: {request.text}"

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        raw_text = response.content[0].text.strip()

        # Parse JSON response
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            return AIParseResult(
                success=False,
                confidence=0,
                fallback=True,
                error="AI returned invalid JSON. Please use manual entry.",
                raw_text=raw_text
            )

        # Check success flag
        if not parsed.get("success", False):
            return AIParseResult(
                success=False,
                confidence=parsed.get("confidence", 0),
                fallback=True,
                error=parsed.get("error", "AI could not parse the expense")
            )

        # Check confidence threshold
        confidence = parsed.get("confidence", 0)
        if confidence < 0.6:
            return AIParseResult(
                success=False,
                confidence=confidence,
                fallback=True,
                error=f"Low confidence ({confidence}). Please use manual entry."
            )

        # Match names to actual user IDs
        payer_name = parsed.get("payer_name", "")
        payer_member = find_user_by_name(payer_name, members)
        if not payer_member:
            return AIParseResult(
                success=False,
                confidence=confidence,
                fallback=True,
                error=f"Could not find payer '{payer_name}' in group members"
            )

        # Match share names to user IDs
        shares_raw = parsed.get("shares", [])
        resolved_shares = []
        for share in shares_raw:
            member = find_user_by_name(share["name"], members)
            if not member:
                return AIParseResult(
                    success=False,
                    confidence=confidence,
                    fallback=True,
                    error=f"Could not find member '{share['name']}' in group"
                )
            resolved_shares.append(AIShareResult(
                user_id=member["id"],
                user_name=member["name"],
                share_paise=share["share_paise"]
            ))

        # Validate shares sum
        total_shares = sum(s.share_paise for s in resolved_shares)
        amount_paise = parsed.get("amount_paise", 0)
        if total_shares != amount_paise:
            return AIParseResult(
                success=False,
                confidence=confidence,
                fallback=True,
                error=f"Shares don't add up. Got {total_shares} paise, expected {amount_paise} paise."
            )

        return AIParseResult(
            success=True,
            confidence=confidence,
            payer_id=payer_member["id"],
            payer_name=payer_member["name"],
            amount_paise=amount_paise,
            description=parsed.get("description", ""),
            date=parsed.get("date"),
            split_mode=parsed.get("split_mode", "custom"),
            shares=resolved_shares
        )

    except Exception as e:
        return AIParseResult(
            success=False,
            confidence=0,
            fallback=True,
            error=f"AI service unavailable. Please use manual entry."
        )

@router.post("/parse-bill", response_model=BillParseResult)
def parse_bill_text(request: BillParseRequest, db: Session = Depends(get_db)):
    # Check group exists
    group = db.query(Group).filter(Group.id == request.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    system_prompt = """You are a bill parsing assistant.
Extract line items from restaurant bills, receipts, or any bill text.

You must respond with ONLY a valid JSON object. No explanation, no markdown, no extra text.
The JSON must match this exact schema:
{
    "success": true,
    "items": [
        {"item_name": "Butter Chicken", "amount_paise": 35000, "quantity": 1},
        {"item_name": "Naan", "amount_paise": 6000, "quantity": 2}
    ],
    "subtotal_paise": 41000,
    "tax_paise": 4100,
    "total_paise": 45100
}

Rules:
- amount_paise = item price in rupees multiplied by 100
- quantity is the number of that item ordered
- If you cannot parse the bill, return {"success": false, "error": "reason"}
- Include tax, service charge as separate items if mentioned
- subtotal_paise is before tax, total_paise is the final amount"""

    user_prompt = f"Parse this bill:\n{request.bill_text}"

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        raw_text = response.content[0].text.strip()

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            return BillParseResult(
                success=False,
                fallback=True,
                error="AI returned invalid response. Please enter manually."
            )

        if not parsed.get("success", False):
            return BillParseResult(
                success=False,
                fallback=True,
                error=parsed.get("error", "Could not parse bill")
            )

        items = [
            BillItem(
                item_name=item["item_name"],
                amount_paise=item["amount_paise"],
                quantity=item.get("quantity", 1)
            )
            for item in parsed.get("items", [])
        ]

        return BillParseResult(
            success=True,
            items=items,
            subtotal_paise=parsed.get("subtotal_paise"),
            tax_paise=parsed.get("tax_paise"),
            total_paise=parsed.get("total_paise")
        )

    except Exception as e:
        return BillParseResult(
            success=False,
            fallback=True,
            error="AI service unavailable. Please enter manually."
        )

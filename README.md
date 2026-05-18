# PROMPTS.md — AI Prompt Log

## 1. Production Prompts (Inside the App)

### 1.1 Natural Language Expense Parser
**File**: `backend/app/routers/ai_parse.py`  
**Endpoint**: `POST /api/ai/parse-expense`

**System Prompt**:
```
You are an expense parsing assistant for a bill splitting app.
Your job is to extract structured expense information from natural language text.

Group members are: {member_list_str}
The person currently logged in is: {current_user_name}
Today's date is: {today}
Default currency: INR (Indian Rupees)

You must respond with ONLY a valid JSON object. No explanation, no markdown, no extra text.
The JSON must match this exact schema:
{
    "success": true,
    "confidence": 0.95,
    "payer_name": "Aman",
    "amount_paise": 240000,
    "description": "Dinner at restaurant",
    "date": "2025-01-15T20:00:00",
    "split_mode": "custom",
    "shares": [
        {"name": "Aman", "share_paise": 100000},
        {"name": "Priya", "share_paise": 140000}
    ]
}

Rules:
- amount_paise = amount in rupees multiplied by 100 (so ₹24 = 2400 paise)
- shares must sum exactly to amount_paise
- split_mode is one of: equal, subset, custom, weighted
- confidence is between 0 and 1 (how sure you are about the parsing)
- If you cannot parse the text reliably, return {"success": false, "confidence": 0, "error": "reason"}
- Only use names from the group members list
- If "me" or "I" is used, it refers to {current_user_name}
- date should be ISO format, use today if not specified
```

**Why I wrote it this way**:
- "ONLY a valid JSON object. No explanation, no markdown" — LLMs default to wrapping JSON in ```json blocks or adding preamble. This breaks `json.loads()`. Explicit instruction eliminates it.
- Injecting `member_list_str` into the system prompt — Claude can only match names to real group members. Prevents hallucinated names like "John" appearing in an Indian group.
- `confidence` field — allows us to reject low-confidence parses (< 0.6 threshold) before they reach the user. Claude is calibrated enough that 0.6 is a reliable cutoff.
- `"me" or "I" refers to {current_user_name}` — most natural language expense descriptions use first person. This maps it correctly without ambiguity.
- Amount in paise in the schema — if I asked Claude to return rupees as a float, I'd have to multiply and round. Asking for paise directly keeps all math integer.

---

### 1.2 Bill Text Parser
**File**: `backend/app/routers/ai_parse.py`  
**Endpoint**: `POST /api/ai/parse-bill`

**System Prompt**:
```
You are a bill parsing assistant.
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
- subtotal_paise is before tax, total_paise is the final amount
```

**Why I wrote it this way**:
- Separate subtotal/tax/total fields — restaurant bills in India always have GST (5% or 18%). Separating them lets the UI show the breakdown and lets users verify the total before assigning items.
- `quantity` field — a bill might say "Naan x3 - 180". Storing quantity=3 and amount=60 per naan lets the UI show per-item price clearly.
- No group member names injected here — bill parsing is item extraction only. Member assignment happens in the frontend UI after parsing. Keeps the prompt focused.

---

## 2. Coding Assistant Prompts (Used to Build the App)

| What I asked | Tool | What I got |
|---|---|---|
| "Build a FastAPI backend for expense splitting with SQLAlchemy models for users, groups, expenses, expense_shares, settlements" | Claude | Complete models.py with all 6 tables, UUID primary keys, soft delete pattern |
| "Write the settle-up algorithm — minimum transactions to settle group debts" | Claude | Greedy two-pointer algorithm with creditors/debtors lists, O(n log n) |
| "Write Pydantic schemas with validator that rejects if shares don't sum to total" | Claude | schemas.py with @validator on shares_must_sum_to_total |
| "Build React frontend with Tailwind, dark theme, group list, group detail with tabs for expenses/balances/settle-up/AI" | Claude | Complete frontend pages and components |
| "Fix Promise.all failure — if one API call fails the whole group detail crashes" | Claude | Sequential async/await with individual try/catch per call |

**What I reviewed and changed**:
- The seed data had a float multiplication bug for paise conversion — changed `amount_rupees * 100` to `int(amount_rupees * 100)` with explicit `Math.round` equivalent
- The AI prompt initially didn't specify "no markdown" — Claude was wrapping JSON in backticks, breaking the parser. Added explicit instruction.
- The settle-up algorithm initially used `dict.items()` without sorting — added `.sort(key=lambda x: x[1], reverse=True)` to guarantee minimum transactions 

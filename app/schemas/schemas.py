from pydantic import BaseModel, EmailStr, condecimal
from typing import Optional, List
from datetime import datetime

# ── Group ──────────────────────────────────────────────
class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None

class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

# ── Member ─────────────────────────────────────────────
class MemberCreate(BaseModel):
    name: str
    email: Optional[str] = None

class MemberResponse(BaseModel):
    id: int
    group_id: int
    name: str
    email: Optional[str]

# ── Expense ────────────────────────────────────────────
class SplitEntry(BaseModel):
    member_id: int
    share: float                   # exact amount this member owes

class ExpenseCreate(BaseModel):
    paid_by: int                   # member_id who paid
    description: str
    amount: float
    splits: List[SplitEntry]       # must sum to amount

class ExpenseResponse(BaseModel):
    id: int
    group_id: int
    paid_by: int
    description: str
    amount: float
    created_at: datetime
    splits: List[SplitEntry]

# ── Settlement ─────────────────────────────────────────
class Transaction(BaseModel):
    from_member: str               # name of person who owes
    to_member: str                 # name of person to pay
    amount: float

class SettlementResponse(BaseModel):
    group_id: int
    transactions: List[Transaction]
    total_transactions: int

"""
Pydantic Schemas for Request/Response Validation
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal


# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Note Schemas
class NoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    deadline: Optional[date] = None
    in_calendar: bool = False
    is_archived: bool = False

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[str] = None
    deadline: Optional[date] = None
    in_calendar: Optional[bool] = None
    is_archived: Optional[bool] = None

class NoteResponse(NoteBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# Calendar Schemas
class CalendarEventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    date: date
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")

class CalendarEventCreate(CalendarEventBase):
    note_id: Optional[int] = None

class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date] = None
    priority: Optional[str] = None

class CalendarEventResponse(CalendarEventBase):
    id: int
    user_id: int
    note_id: Optional[int] = None
    caldav_uid: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


# Category Schemas
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default="#3B82F6", pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True


# Transaction Schemas
class TransactionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0)
    type: str = Field(..., pattern="^(income|expense)$")
    date: date
    category_id: Optional[int] = None
    is_recurring: bool = False
    recurring_interval: Optional[str] = None
    notes: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[Decimal] = None
    type: Optional[str] = None
    date: Optional[date] = None
    category_id: Optional[int] = None
    is_recurring: Optional[bool] = None
    recurring_interval: Optional[str] = None
    notes: Optional[str] = None

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    category: Optional[CategoryResponse] = None
    class Config:
        from_attributes = True

class FinanceSummary(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    by_category: Optional[List[dict]] = None


# Budget Schemas
class BudgetBase(BaseModel):
    name: str
    amount: Decimal
    period: str
    start_date: date
    end_date: Optional[date] = None
    category_id: Optional[int] = None
    alert_threshold: int = 80

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[Decimal] = None
    period: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    category_id: Optional[int] = None
    alert_threshold: Optional[int] = None

class BudgetResponse(BudgetBase):
    id: int
    user_id: int
    spent: Optional[Decimal] = None
    remaining: Optional[Decimal] = None
    percentage: Optional[int] = None
    created_at: datetime
    category: Optional[CategoryResponse] = None
    class Config:
        from_attributes = True


# Savings Schemas
class SavingsGoalBase(BaseModel):
    name: str
    target_amount: Decimal
    current_amount: Decimal = Decimal("0.00")
    deadline: Optional[date] = None
    icon: Optional[str] = None

class SavingsGoalCreate(SavingsGoalBase):
    pass

class SavingsGoalUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[Decimal] = None
    current_amount: Optional[Decimal] = None
    deadline: Optional[date] = None
    icon: Optional[str] = None

class SavingsGoalResponse(SavingsGoalBase):
    id: int
    user_id: int
    percentage: Optional[int] = None
    created_at: datetime
    class Config:
        from_attributes = True


# Mail Schemas
class MailAccountBase(BaseModel):
    email_address: EmailStr
    display_name: Optional[str] = None
    provider: str
    imap_server: str
    imap_port: int = 993
    imap_use_ssl: bool = True
    smtp_server: str
    smtp_port: int = 587
    smtp_use_tls: bool = True

class MailAccountCreate(MailAccountBase):
    password: str

class MailAccountUpdate(BaseModel):
    display_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class MailAccountResponse(MailAccountBase):
    id: int
    user_id: int
    is_active: bool
    last_sync: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True


class EmailResponse(BaseModel):
    id: int
    account_id: int
    message_id: str
    subject: Optional[str] = None
    sender: str
    recipients: Optional[str] = None
    date: datetime
    is_read: bool
    is_starred: bool
    is_archived: bool
    folder: str
    has_attachments: bool
    body_text: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class EmailSend(BaseModel):
    to: List[EmailStr]
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    subject: str
    body: str
    is_html: bool = False

class EmailUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_starred: Optional[bool] = None
    is_archived: Optional[bool] = None
    folder: Optional[str] = None

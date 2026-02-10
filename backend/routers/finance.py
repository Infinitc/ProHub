from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from decimal import Decimal
import models, schemas
from database import get_db
from dependencies import get_current_user

router = APIRouter()

@router.post("/categories", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(cat: schemas.CategoryCreate, db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    c = models.Category(**cat.model_dump(), user_id=cu.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@router.get("/categories", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    return db.query(models.Category).filter(models.Category.user_id == cu.id).all()

@router.post("/transactions", response_model=schemas.TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(t: schemas.TransactionCreate, db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    tr = models.Transaction(**t.model_dump(), user_id=cu.id)
    db.add(tr)
    db.commit()
    db.refresh(tr)
    return tr

@router.get("/transactions", response_model=List[schemas.TransactionResponse])
def get_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    return db.query(models.Transaction).filter(models.Transaction.user_id == cu.id).order_by(models.Transaction.date.desc()).offset(skip).limit(limit).all()

@router.get("/summary", response_model=schemas.FinanceSummary)
def get_summary(db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    q = db.query(models.Transaction).filter(models.Transaction.user_id == cu.id)
    income = q.filter(models.Transaction.type == "income").with_entities(func.sum(models.Transaction.amount)).scalar() or Decimal("0.00")
    expense = q.filter(models.Transaction.type == "expense").with_entities(func.sum(models.Transaction.amount)).scalar() or Decimal("0.00")
    return {"total_income": income, "total_expense": expense, "balance": income - expense, "by_category": []}

@router.post("/budgets", response_model=schemas.BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(b: schemas.BudgetCreate, db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    budget = models.Budget(**b.model_dump(), user_id=cu.id)
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget

@router.get("/budgets", response_model=List[schemas.BudgetResponse])
def get_budgets(db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    return db.query(models.Budget).filter(models.Budget.user_id == cu.id).all()

@router.post("/savings", response_model=schemas.SavingsGoalResponse, status_code=status.HTTP_201_CREATED)
def create_savings(s: schemas.SavingsGoalCreate, db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    goal = models.SavingsGoal(**s.model_dump(), user_id=cu.id)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal

@router.get("/savings", response_model=List[schemas.SavingsGoalResponse])
def get_savings(db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    return db.query(models.SavingsGoal).filter(models.SavingsGoal.user_id == cu.id).all()

from fastapi import APIRouter, Depends, HTTPException, status, Response
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

@router.get("/summary")
async def get_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id)
    
    if start_date:
        query = query.filter(models.Transaction.date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.date <= end_date)
    
    transactions = query.all()
    
    # WICHTIG: Berechnung hinzufügen!
    total_income = sum(float(t.amount) for t in transactions if t.type == "income")
    total_expense = sum(float(t.amount) for t in transactions if t.type == "expense")
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense
    }

@router.delete("/transactions/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db.delete(transaction)
    db.commit()
    return Response(status_code=204)

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

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import get_db
from dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[schemas.SavingsGoalResponse])
def get_savings(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.SavingsGoal).filter(models.SavingsGoal.user_id == current_user.id).order_by(models.SavingsGoal.created_at.desc()).all()

@router.post("/", response_model=schemas.SavingsGoalResponse, status_code=status.HTTP_201_CREATED)
def create_savings(goal: schemas.SavingsGoalCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_goal = models.SavingsGoal(**goal.model_dump(), user_id=current_user.id)
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_savings(goal_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    goal = db.query(models.SavingsGoal).filter(models.SavingsGoal.id == goal_id, models.SavingsGoal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(goal)
    db.commit()
    return Response(status_code=204)

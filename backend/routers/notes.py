from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from dependencies import get_current_user
import models, schemas

router = APIRouter()

@router.post("/", response_model=schemas.NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(note: schemas.NoteCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_note = models.Note(**note.model_dump(), user_id=current_user.id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    if note.in_calendar and note.deadline:
        event = models.CalendarEvent(user_id=current_user.id, note_id=db_note.id, title=note.title, date=note.deadline, priority=note.priority)
        db.add(event)
        db.commit()
    return db_note

@router.get("/", response_model=List[schemas.NoteResponse])
def get_notes(skip: int = 0, limit: int = 100, priority: Optional[str] = None, is_archived: Optional[bool] = None, sort_by: str = "created_at", sort_order: str = "desc", db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Note).filter(models.Note.user_id == current_user.id)
    if priority:
        query = query.filter(models.Note.priority == priority)
    if is_archived is not None:
        query = query.filter(models.Note.is_archived == is_archived)
    if sort_order == "desc":
        query = query.order_by(getattr(models.Note, sort_by).desc())
    else:
        query = query.order_by(getattr(models.Note, sort_by).asc())
    return query.offset(skip).limit(limit).all()

@router.get("/{note_id}", response_model=schemas.NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.user_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.put("/{note_id}", response_model=schemas.NoteResponse)
def update_note(note_id: int, note_update: schemas.NoteUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.user_id == current_user.id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    for field, value in note_update.model_dump(exclude_unset=True).items():
        setattr(db_note, field, value)
    db.commit()
    db.refresh(db_note)
    return db_note

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.user_id == current_user.id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(db_note)
    db.commit()
    return None

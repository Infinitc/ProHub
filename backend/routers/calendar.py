from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import uuid, models, schemas
from database import get_db
from dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.CalendarEventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event: schemas.CalendarEventCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_event = models.CalendarEvent(**event.model_dump(), user_id=current_user.id, caldav_uid=str(uuid.uuid4()))
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.get("/", response_model=List[schemas.CalendarEventResponse])
def get_events(start_date: Optional[date] = None, end_date: Optional[date] = None, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.CalendarEvent).filter(models.CalendarEvent.user_id == current_user.id)
    if start_date:
        query = query.filter(models.CalendarEvent.date >= start_date)
    if end_date:
        query = query.filter(models.CalendarEvent.date <= end_date)
    return query.order_by(models.CalendarEvent.date.asc()).all()

@router.get("/export/ics")
def export_ics(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    events = db.query(models.CalendarEvent).filter(models.CalendarEvent.user_id == current_user.id).all()
    ics = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//ProHub//Calendar//EN\r\nCALSCALE:GREGORIAN\r\n"
    for e in events:
        ics += f"BEGIN:VEVENT\r\nUID:{e.caldav_uid or uuid.uuid4()}\r\nDTSTART;VALUE=DATE:{e.date.strftime('%Y%m%d')}\r\nSUMMARY:{e.title}\r\nEND:VEVENT\r\n"
    ics += "END:VCALENDAR\r\n"
    return Response(content=ics, media_type="text/calendar", headers={"Content-Disposition": f"attachment; filename=prohub-calendar.ics"})

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    event = db.query(models.CalendarEvent).filter(models.CalendarEvent.id == event_id, models.CalendarEvent.user_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404)
    db.delete(event)
    db.commit()
    return None

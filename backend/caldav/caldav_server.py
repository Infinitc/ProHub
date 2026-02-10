from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
import uuid, models
from database import get_db
from dependencies import get_current_user

router = APIRouter()

@router.options("/{path:path}")
async def caldav_options(path: str):
    return Response(headers={"DAV": "1, calendar-access", "Allow": "OPTIONS, GET, PUT, DELETE, PROPFIND"})

@router.api_route("/{path:path}", methods=["PROPFIND"])
async def caldav_propfind(request: Request, db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    events = db.query(models.CalendarEvent).filter(models.CalendarEvent.user_id == cu.id).all()
    xml = '<?xml version="1.0"?><D:multistatus xmlns:D="DAV:">'
    for e in events:
        uid = e.caldav_uid or str(uuid.uuid4())
        xml += f'<D:response><D:href>/caldav/calendar/{uid}.ics</D:href><D:propstat><D:status>HTTP/1.1 200 OK</D:status></D:propstat></D:response>'
    xml += '</D:multistatus>'
    return Response(content=xml, media_type="application/xml", status_code=207)

@router.get("/calendar/{uid}.ics")
async def get_event(uid: str, db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    event = db.query(models.CalendarEvent).filter(models.CalendarEvent.caldav_uid == uid, models.CalendarEvent.user_id == cu.id).first()
    if not event:
        return Response(status_code=404)
    ics = f"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:{uid}\r\nDTSTART;VALUE=DATE:{event.date.strftime('%Y%m%d')}\r\nSUMMARY:{event.title}\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
    return Response(content=ics, media_type="text/calendar")

@router.put("/calendar/{uid}.ics")
async def create_event(uid: str, request: Request, db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    body = await request.body()
    event = models.CalendarEvent(user_id=cu.id, caldav_uid=uid, title="Imported Event", date=models.date.today(), priority="medium")
    db.add(event)
    db.commit()
    return Response(status_code=201)

@router.delete("/calendar/{uid}.ics")
async def delete_event(uid: str, db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    event = db.query(models.CalendarEvent).filter(models.CalendarEvent.caldav_uid == uid, models.CalendarEvent.user_id == cu.id).first()
    if event:
        db.delete(event)
        db.commit()
    return Response(status_code=204)

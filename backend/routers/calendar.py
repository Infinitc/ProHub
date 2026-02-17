"""
Calendar Router with automatic CalDAV sync to Radicale
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import uuid, models, schemas, logging, requests
from requests.auth import HTTPBasicAuth
from database import get_db
from dependencies import get_current_user
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# ─── Radicale config ────────────────────────────────────────────────────────
RADICALE_INTERNAL = "http://127.0.0.1:5232"   # direct internal connection
CALDAV_PASSWORD   = getattr(settings, "CALDAV_PASSWORD", "12345")


def _ics_content(event: models.CalendarEvent) -> str:
    """Build a minimal VCALENDAR/VEVENT iCal string."""
    uid  = event.caldav_uid or str(uuid.uuid4())
    dts  = event.date.strftime("%Y%m%d")
    desc = (event.description or "").replace("\n", "\\n")
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//PolyHub//Calendar//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTART;VALUE=DATE:{dts}\r\n"
        f"SUMMARY:{event.title}\r\n"
        f"DESCRIPTION:{desc}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


def sync_to_radicale(username: str, event: models.CalendarEvent) -> bool:
    """PUT a single event into Radicale. Returns True on success."""
    uid  = event.caldav_uid or str(uuid.uuid4())
    url  = f"{RADICALE_INTERNAL}/{username}/calendar/{uid}.ics"
    ics  = _ics_content(event)
    try:
        r = requests.put(
            url,
            data=ics.encode("utf-8"),
            auth=HTTPBasicAuth(username, CALDAV_PASSWORD),
            headers={"Content-Type": "text/calendar; charset=utf-8"},
            timeout=5,
        )
        if r.status_code in (201, 204):
            logger.info(f"CalDAV sync OK: {url} → {r.status_code}")
            return True
        logger.warning(f"CalDAV sync failed: {url} → {r.status_code} {r.text[:200]}")
        return False
    except Exception as e:
        logger.warning(f"CalDAV sync error: {e}")
        return False


def delete_from_radicale(username: str, caldav_uid: str) -> bool:
    """DELETE an event from Radicale."""
    url = f"{RADICALE_INTERNAL}/{username}/calendar/{caldav_uid}.ics"
    try:
        r = requests.delete(
            url,
            auth=HTTPBasicAuth(username, CALDAV_PASSWORD),
            timeout=5,
        )
        logger.info(f"CalDAV delete: {url} → {r.status_code}")
        return r.status_code in (200, 204, 404)
    except Exception as e:
        logger.warning(f"CalDAV delete error: {e}")
        return False


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/", response_model=schemas.CalendarEventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event: schemas.CalendarEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    uid = str(uuid.uuid4())
    db_event = models.CalendarEvent(
        **event.model_dump(),
        user_id=current_user.id,
        caldav_uid=uid,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    # Sync to Radicale (non-blocking — failure doesn't break the response)
    sync_to_radicale(current_user.username, db_event)

    return db_event


@router.get("/", response_model=List[schemas.CalendarEventResponse])
def get_events(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.CalendarEvent).filter(
        models.CalendarEvent.user_id == current_user.id
    )
    if start_date:
        query = query.filter(models.CalendarEvent.date >= start_date)
    if end_date:
        query = query.filter(models.CalendarEvent.date <= end_date)
    return query.order_by(models.CalendarEvent.date.asc()).all()


@router.get("/export/ics")
def export_ics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    events = db.query(models.CalendarEvent).filter(
        models.CalendarEvent.user_id == current_user.id
    ).all()

    ics = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//PolyHub//Calendar//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
    )
    for e in events:
        dts = e.date.strftime("%Y%m%d")
        ics += (
            "BEGIN:VEVENT\r\n"
            f"UID:{e.caldav_uid or uuid.uuid4()}\r\n"
            f"DTSTART;VALUE=DATE:{dts}\r\n"
            f"SUMMARY:{e.title}\r\n"
            "END:VEVENT\r\n"
        )
    ics += "END:VCALENDAR\r\n"

    return Response(
        content=ics,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=polyhub-calendar.ics"},
    )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    event = db.query(models.CalendarEvent).filter(
        models.CalendarEvent.id == event_id,
        models.CalendarEvent.user_id == current_user.id,
    ).first()
    if not event:
        raise HTTPException(status_code=404)

    # Remove from Radicale first
    if event.caldav_uid:
        delete_from_radicale(current_user.username, event.caldav_uid)

    db.delete(event)
    db.commit()
    return None


@router.post("/sync-all", status_code=status.HTTP_200_OK)
def sync_all_events(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Re-sync ALL events for this user to Radicale. Useful after setup."""
    events = db.query(models.CalendarEvent).filter(
        models.CalendarEvent.user_id == current_user.id
    ).all()

    ok, fail = 0, 0
    for e in events:
        if not e.caldav_uid:
            e.caldav_uid = str(uuid.uuid4())
            db.commit()
            db.refresh(e)
        if sync_to_radicale(current_user.username, e):
            ok += 1
        else:
            fail += 1

    return {"synced": ok, "failed": fail, "total": len(events)}

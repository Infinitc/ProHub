from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, imaplib, smtplib, email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from database import get_db
from dependencies import get_current_user

router = APIRouter()

@router.post("/accounts", response_model=schemas.MailAccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(acc: schemas.MailAccountCreate, db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    db_acc = models.MailAccount(**acc.model_dump(), user_id=cu.id)
    db.add(db_acc)
    db.commit()
    db.refresh(db_acc)
    return db_acc

@router.get("/accounts", response_model=List[schemas.MailAccountResponse])
def get_accounts(db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    return db.query(models.MailAccount).filter(models.MailAccount.user_id == cu.id).all()

@router.post("/accounts/{account_id}/sync")
def sync_emails(account_id: int, limit: int = 50, db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    acc = db.query(models.MailAccount).filter(models.MailAccount.id == account_id, models.MailAccount.user_id == cu.id).first()
    if not acc:
        raise HTTPException(status_code=404)
    try:
        mail = imaplib.IMAP4_SSL(acc.imap_server, acc.imap_port) if acc.imap_use_ssl else imaplib.IMAP4(acc.imap_server, acc.imap_port)
        mail.login(acc.email_address, acc.password)
        mail.select("INBOX")
        _, msgs = mail.search(None, 'ALL')
        synced = 0
        for num in msgs[0].split()[-limit:]:
            _, data = mail.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            mid = msg.get('Message-ID', '')
            if db.query(models.Email).filter(models.Email.message_id == mid).first():
                continue
            db_email = models.Email(account_id=acc.id, message_id=mid, subject=msg.get('Subject', ''), sender=msg.get('From', ''), recipients=msg.get('To', ''), date=datetime.utcnow(), folder="INBOX", has_attachments=False, attachment_count=0)
            db.add(db_email)
            synced += 1
        acc.last_sync = datetime.utcnow()
        db.commit()
        mail.close()
        mail.logout()
        return {"synced": synced}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emails", response_model=List[schemas.EmailResponse])
def get_emails(account_id: Optional[int] = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    q = db.query(models.Email).join(models.MailAccount).filter(models.MailAccount.user_id == cu.id)
    if account_id:
        q = q.filter(models.Email.account_id == account_id)
    return q.order_by(models.Email.date.desc()).offset(skip).limit(limit).all()

@router.post("/accounts/{account_id}/send")
def send_email(account_id: int, email_data: schemas.EmailSend, db: Session = Depends(get_db), cu: models.User = Depends(get_current_user)):
    acc = db.query(models.MailAccount).filter(models.MailAccount.id == account_id, models.MailAccount.user_id == cu.id).first()
    if not acc:
        raise HTTPException(status_code=404)
    try:
        msg = MIMEMultipart()
        msg['From'] = acc.email_address
        msg['To'] = ', '.join(email_data.to)
        msg['Subject'] = email_data.subject
        msg.attach(MIMEText(email_data.body, 'html' if email_data.is_html else 'plain'))
        smtp = smtplib.SMTP(acc.smtp_server, acc.smtp_port)
        if acc.smtp_use_tls:
            smtp.starttls()
        smtp.login(acc.email_address, acc.password)
        smtp.sendmail(acc.email_address, email_data.to, msg.as_string())
        smtp.quit()
        return {"message": "Email sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

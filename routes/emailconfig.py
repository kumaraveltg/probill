from fastapi import APIRouter, HTTPException, Depends, Query 
from sqlmodel import Session, select, SQLModel, Field, func, and_
from .db import engine, get_session
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER, JSON
from pydantic import EmailStr, validator, BaseModel
from typing import List, Optional 
from datetime import datetime, date    
from routes.utils import encrypt_password, decrypt_password
import smtplib 
from email.message import EmailMessage
from routes.company import Company


router = APIRouter(tags=["Email"])

class EmailConfig(SQLModel, table=True):
    __tablename__ = "email_config"
    __table_args__ = {"extend_existing": True} 
    id: int | None = Field(default=None, primary_key=True)
    companyid: Optional[int] = None
    companyno: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[str] = None
    use_tls: bool = Field(default=True)
    email_from: EmailStr 
    email_password: Optional[str] = None
    createdon: datetime = Field(default_factory=datetime.now) 
   

class EmailSetting(SQLModel, table=True):
    __tablename__ = "email_settings"
    __table_args__ = {"extend_existing": True}  
    id: int | None = Field(default=None, primary_key=True) 
    companyid: Optional[int] = None
    companyno: Optional[str] = None
    email_from: EmailStr
    email_to: EmailStr
    email_cc: Optional[str] = None
    email_bcc: Optional[str] = None
    subject: Optional[str] = None
    body: str
    attachment_path: Optional[str] = None
    sent_status: bool = Field(default=False)
    sent_at: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})  
    createdon: datetime = Field(default_factory=datetime.now) 
    error: Optional[str] = None
    createdby: Optional[str] = None

class PostemailConfig(BaseModel):
    id: Optional[int] = None
    companyid: Optional[int] = None
    companyno: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[str] = None
    use_tls: bool = Field(default=True)
    email_from: Optional[str] = None 
    email_password: Optional[str] = None 
    createdon: datetime = Field(default_factory=datetime.now) 
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class TestEmailConfig(BaseModel): 
    smtp_host: str
    smtp_port: str
    use_tls: bool = Field(default=True) 
    email_from: str  # Changed from Optional to required 
    email_password: str  # Changed from Optional to required
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }

class PostEmailSetting(BaseModel):
    id: Optional[int] = None 
    companyid: Optional[int] = None
    companyno: Optional[str] = None
    email_from: EmailStr
    email_to: EmailStr
    email_cc: Optional[str] = None
    email_bcc: Optional[str] = None
    subject: Optional[str] = None
    body: str
    attachment_path: Optional[str] = None
    sent_status: bool = Field(default=False)
    sent_at: datetime 
    createdon: datetime  
    error: Optional[str] = None
    createdby: Optional[str] = None
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
    }


@router.post("/addemailset", response_model=PostemailConfig)
def create_email_setting(es: PostemailConfig):
    with Session(engine) as session:
        email_dict = es.dict() 
        email_data = EmailConfig(**email_dict)
        session.add(email_data)
        session.commit()
        session.refresh(email_data)

        email_config_data = PostemailConfig.from_orm(email_data)
        
        return email_config_data   
    
@router.post("/updateemailcon/{emailconid}", response_model=PostemailConfig)
def update_emailconfig(emailconid: int, ec_update: PostemailConfig, session: Session = Depends(get_session)):

    db_email = session.get(EmailConfig, emailconid)
    if not db_email:
        raise HTTPException(status_code=404, detail="Email config not found")

    update_data = ec_update.model_dump(exclude_unset=True)

    # Do not overwrite ID
    update_data.pop("id", None)

    for key, value in update_data.items():
        setattr(db_email, key, value)

    session.add(db_email)
    session.commit()
    session.refresh(db_email)

    return db_email


    
@router.post("/test-smtp")
def test_smtp_connection(es: TestEmailConfig):
    config = {
        "host": es.smtp_host.strip(),
        "port": int(es.smtp_port),  # Convert to int
        "username": es.email_from,  # Fixed: use email_username
        "password": es.email_password.strip(),
        "use_tls": es.use_tls
    }
    print("SMTP CONFIG VALUES:", config) 
    
    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=10) as smtp:
            smtp.ehlo()
            if config["use_tls"]:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(config["username"], config["password"])
        return {"ok": True, "msg": f"✅ SMTP login successful for {config['username']}"} 

    except smtplib.SMTPAuthenticationError as e:
        return {
            "ok": False,
            "msg": "❌ Authentication failed: Invalid username or password (check App Password / SMTP settings)",
            "details": str(e)
        }
    except smtplib.SMTPConnectError:
        return {"ok": False, "msg": "❌ Connection failed: Cannot connect to SMTP server"}
    except smtplib.SMTPException as e:
        return {"ok": False, "msg": f"SMTP error: {str(e)}"}
    except Exception as e:
        return {"ok": False, "msg": f"Unexpected error: {str(e)}"}
    

@router.post("/send-test-email")
def send_test_email(es: TestEmailConfig):

    try:
        msg = EmailMessage()
        msg["From"] = es.email_from
        msg["To"] = es.email_from         # send to same email
        msg["Subject"] = "Bill Studio Test Email"
        msg.set_content("This is a test email from your Bill Studio SMTP settings.")

        with smtplib.SMTP(es.smtp_host, int(es.smtp_port), timeout=10) as smtp:
            smtp.ehlo()
            if es.use_tls:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(es.email_from, es.email_password)
            smtp.send_message(msg)

        return {"ok": True, "msg": "✅ Test email sent successfully!"}

    except smtplib.SMTPAuthenticationError:
        return {"ok": False, "msg": "❌ Authentication failed — check SMTP username/password"}

    except Exception as e:
        return {"ok": False, "msg": f"❌ Error sending test email: {str(e)}"}



@router.post("/sendpending")
def send_pending_emails():
    with Session(engine) as session:
        config = session.query(EmailConfig).order_by(EmailConfig.id.desc()).first()
        if not config:
            raise HTTPException(status_code=400, detail="Email config not found")

        # Use email_username if available, otherwise use email_from
        smtp_username =  config.email_from
        smtp_password = config.email_password
        
        pending = session.query(EmailSetting).filter_by(sent_status=False).all()

        sent_count = 0
        failed_emails = []

        for email in pending:
            try:
                print("------------------------------------------------")
                print("SMTP USER:", smtp_username)
                print("SMTP HOST:", config.smtp_host)
                print("SMTP PORT:", config.smtp_port)
                print("Sending To:", email.email_to)
                print("Subject:", email.subject)
                print("------------------------------------------------")

                msg = EmailMessage()
                msg["From"] = config.email_from  # Display name
                msg["To"] = email.email_to
                msg["Subject"] = email.subject
                
                # Add CC if present
                if email.email_cc:
                    msg["Cc"] = email.email_cc
                
                # Add BCC if present
                if email.email_bcc:
                    msg["Bcc"] = email.email_bcc
                
                msg.set_content(email.body)

                with smtplib.SMTP(config.smtp_host, int(config.smtp_port), timeout=10) as smtp:
                    smtp.ehlo()
                    if config.use_tls:
                        smtp.starttls()
                        smtp.ehlo()

                    smtp.login(smtp_username, smtp_password)
                    smtp.send_message(msg)

                email.sent_status = True
                email.sent_at = datetime.utcnow()
                email.error = None
                session.commit()
                sent_count += 1
                print(f"✅ Successfully sent to {email.email_to}")

            except Exception as e:
                error_msg = str(e)
                print(f"❌ Failed to send to {email.email_to}: {error_msg}")
                
                # Store error in database
                email.error = error_msg
                session.commit()
                
                failed_emails.append({
                    "email_to": email.email_to,
                    "error": error_msg
                })

        return {
            "status": "success" if sent_count > 0 else "failed",
            "emails_sent": sent_count,
            "total_pending": len(pending),
            "failed": failed_emails
        }
    
@router.get("/getemailconfig/{companyid}", response_model=PostemailConfig | None)
def get_emailconfig(companyid: int, session: Session = Depends(get_session)):

    # Fetch email config for this company
    result = session.exec(
        select(EmailConfig).where(EmailConfig.companyid == companyid)
    ).first()

    if not result:
        return None  # React handles empty form

    # Fetch company details (optional)
    company = session.exec(
        select(Company).where(Company.id == companyid)
    ).first()

    # Attach company fields
    response_data = PostemailConfig.model_validate(result)
    response_data.companyno = company.companyno if company else None
    

    return response_data
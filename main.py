import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import smtplib
from email.message import EmailMessage

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    message: str


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.post("/api/contact")
def contact(req: ContactRequest):
    recipient = os.getenv("RECIPIENT_EMAIL", "kevinsuyadi2017@gmail.com")
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

    subject = f"FastDevp Contact — {req.name}"
    body = f"""
New contact from FastDevp

Name: {req.name}
Email: {req.email}

Message:
{req.message}
""".strip()

    # Build email
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = gmail_user if gmail_user else req.email
    msg["To"] = recipient
    msg["Reply-To"] = req.email
    msg.set_content(body)

    # If credentials are present, send via Gmail SMTP
    if gmail_user and gmail_pass:
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.ehlo()
                server.starttls()
                server.login(gmail_user, gmail_pass)
                server.send_message(msg)
            return {"status": "sent"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Email send failed: {str(e)}")

    # Fallback: no credentials configured — log the email for development
    print("[Contact Fallback] Email not sent (missing GMAIL_USER/GMAIL_APP_PASSWORD). Message logged below:")
    print("To:", recipient)
    print("Subject:", subject)
    print("Body:\n", body)
    return {"status": "queued", "note": "Email not sent (missing credentials). Configure GMAIL_USER and GMAIL_APP_PASSWORD to enable sending."}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

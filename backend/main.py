from fastapi import FastAPI, Form, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import shutil

from .database import get_db, engine, Base
from .model import Complaint
from ml.predict import predict_complaint

from .automation import (
    process_complaint,
    check_overdue_complaint
)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# UPLOADS
# =========================================================

UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# =========================================================
# DEPARTMENT MAP
# =========================================================

DEPARTMENT_MAP = {
    "Sanitation": "Municipal Sanitation Department",
    "Street Lighting": "Electrical / Municipal Department",
    "Certificates": "Citizen Services Department",
    "Water Supply": "Water Supply Department",
    "Electricity": "Electricity Department",
    "Welfare Scheme": "Social Welfare Department",
    "Public Health": "Public Health Department",
    "Public Transport": "Transport Department",
    "Road Damage": "Public Works Department",
    "Drainage": "Municipal Drainage Department"
}


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "Public Service API is running"
    }


# =========================================================
# CREATE COMPLAINT
# =========================================================

@app.post("/complaints")
def create_complaint(
    complaint_text: str = Form(...),
    location: str = Form(...),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # AI CLASSIFICATION
    # -----------------------------------------------------

    category, confidence = predict_complaint(
        complaint_text
    )


    # -----------------------------------------------------
    # DEPARTMENT
    # -----------------------------------------------------

    department = DEPARTMENT_MAP.get(
        category,
        "General Public Services"
    )


    # -----------------------------------------------------
    # PHOTO
    # -----------------------------------------------------

    photo_path = None

    if photo and photo.filename:

        safe_filename = os.path.basename(
            photo.filename
        )

        photo_path = os.path.join(
            UPLOAD_FOLDER,
            safe_filename
        )

        with open(
            photo_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                photo.file,
                buffer
            )


    # -----------------------------------------------------
    # AUTOMATIC PROCESSING
    # -----------------------------------------------------

    automation = process_complaint(
        complaint_text=complaint_text,
        category=category,
        department=department,
        location=location,
        db=db
    )


    # -----------------------------------------------------
    # CREATE DATABASE RECORD
    # -----------------------------------------------------

    complaint = Complaint(

        complaint_text=complaint_text,

        location=location,

        predicted_category=category,

        department=department,

        status="Pending",

        photo_path=photo_path,

        priority=automation["priority"],

        officer_name=automation["officer_name"],

        office_name=automation["office_name"],

        sla_days=automation["sla_days"],

        due_date=automation["due_date"],

        escalation_level=automation["escalation_level"],

        summary=automation["summary"]
    )


    db.add(
        complaint
    )

    db.commit()

    db.refresh(
        complaint
    )


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "complaint_id": complaint.id,

        "category": category,

        "confidence": confidence,

        "department": department,

        "status": complaint.status,

        "priority": complaint.priority,

        "officer_name": complaint.officer_name,

        "office_name": complaint.office_name,

        "sla_days": complaint.sla_days,

        "due_date": complaint.due_date,

        "escalation_level": complaint.escalation_level,

        "summary": complaint.summary,

        "photo": photo_path
    }


# =========================================================
# GET ALL COMPLAINTS
# =========================================================

@app.get("/complaints")
def get_complaints(
    db: Session = Depends(get_db)
):

    complaints = db.query(
        Complaint
    ).all()


    results = []


    for complaint in complaints:

        # Check overdue status
        new_escalation_level = (
            check_overdue_complaint(
                complaint
            )
        )


        if new_escalation_level > (
            complaint.escalation_level or 0
        ):

            complaint.escalation_level = (
                new_escalation_level
            )


        results.append({

            "id": complaint.id,

            "complaint_text":
                complaint.complaint_text,

            "location":
                complaint.location,

            "predicted_category":
                complaint.predicted_category,

            "department":
                complaint.department,

            "status":
                complaint.status,

            "photo_path":
                complaint.photo_path,

            "priority":
                complaint.priority,

            "officer_name":
                complaint.officer_name,

            "office_name":
                complaint.office_name,

            "sla_days":
                complaint.sla_days,

            "due_date":
                complaint.due_date,

            "escalation_level":
                complaint.escalation_level,

            "summary":
                complaint.summary
        })


    db.commit()


    return results


# =========================================================
# UPDATE COMPLAINT STATUS
# =========================================================

@app.put("/complaints/{complaint_id}/status")
def update_complaint_status(
    complaint_id: int,
    status: str,
    db: Session = Depends(get_db)
):

    complaint = db.query(
        Complaint
    ).filter(
        Complaint.id == complaint_id
    ).first()


    if not complaint:

        return {
            "error": "Complaint not found"
        }


    complaint.status = status


    db.commit()

    db.refresh(
        complaint
    )


    return {

        "complaint_id":
            complaint.id,

        "status":
            complaint.status,

        "priority":
            complaint.priority,

        "officer_name":
            complaint.officer_name,

        "office_name":
            complaint.office_name,

        "sla_days":
            complaint.sla_days,

        "due_date":
            complaint.due_date,

        "escalation_level":
            complaint.escalation_level
    }


# =========================================================
# GET SINGLE COMPLAINT
# =========================================================

@app.get("/complaints/{complaint_id}")
def get_complaint_status(
    complaint_id: int,
    db: Session = Depends(get_db)
):

    complaint = db.query(
        Complaint
    ).filter(
        Complaint.id == complaint_id
    ).first()


    if complaint is None:

        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )


    # -----------------------------------------------------
    # CHECK OVERDUE
    # -----------------------------------------------------

    new_escalation_level = (
        check_overdue_complaint(
            complaint
        )
    )


    if new_escalation_level > (
        complaint.escalation_level or 0
    ):

        complaint.escalation_level = (
            new_escalation_level
        )

        db.commit()

        db.refresh(
            complaint
        )


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "complaint_id":
            complaint.id,

        "complaint_text":
            complaint.complaint_text,

        "location":
            complaint.location,

        "category":
            complaint.predicted_category,

        "department":
            complaint.department,

        "status":
            complaint.status,

        "photo_path":
            complaint.photo_path,

        "priority":
            complaint.priority,

        "officer_name":
            complaint.officer_name,

        "office_name":
            complaint.office_name,

        "sla_days":
            complaint.sla_days,

        "due_date":
            complaint.due_date,

        "escalation_level":
            complaint.escalation_level,

        "summary":
            complaint.summary
    }
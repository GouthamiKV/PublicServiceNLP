from fastapi import FastAPI, Form, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import shutil

from .database import get_db, engine, Base
from .model import Complaint
from ml.predict import predict_complaint

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# Create uploads folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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


@app.get("/")
def home():
    return {
        "message": "Public Service Complaint API is running"
    }


# CREATE COMPLAINT
@app.post("/complaints")
def create_complaint(
    complaint_text: str = Form(...),
    location: str = Form(...),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):

    category, confidence = predict_complaint(
        complaint_text
    )

    department = DEPARTMENT_MAP.get(
        category,
        "General Public Services"
    )

    photo_path = None

    # Save photo if uploaded
    if photo and photo.filename:

        safe_filename = os.path.basename(photo.filename)

        photo_path = os.path.join(
            UPLOAD_FOLDER,
            safe_filename
        )

        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(
                photo.file,
                buffer
            )

    complaint = Complaint(
        complaint_text=complaint_text,
        location=location,
        predicted_category=category,
        department=department,
        status="Pending",
        photo_path=photo_path
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return {
        "complaint_id": complaint.id,
        "category": category,
        "confidence": confidence,
        "department": department,
        "status": "Pending",
        "photo": photo_path
    }


# GET ALL COMPLAINTS
@app.get("/complaints")
def get_complaints(
    db: Session = Depends(get_db)
):

    complaints = db.query(Complaint).all()

    return [
        {
            "id": complaint.id,
            "complaint_text": complaint.complaint_text,
            "location": complaint.location,
            "predicted_category": complaint.predicted_category,
            "department": complaint.department,
            "status": complaint.status,
            "photo_path": complaint.photo_path
        }
        for complaint in complaints
    ]


# UPDATE STATUS
@app.put("/complaints/{complaint_id}/status")
def update_complaint_status(
    complaint_id: int,
    status: str,
    db: Session = Depends(get_db)
):

    complaint = db.query(Complaint).filter(
        Complaint.id == complaint_id
    ).first()

    if not complaint:
        return {
            "error": "Complaint not found"
        }

    complaint.status = status

    db.commit()
    db.refresh(complaint)

    return {
        "complaint_id": complaint.id,
        "status": complaint.status
    }


# TRACK SINGLE COMPLAINT
@app.get("/complaints/{complaint_id}")
def get_complaint_status(
    complaint_id: int,
    db: Session = Depends(get_db)
):

    complaint = db.query(Complaint).filter(
        Complaint.id == complaint_id
    ).first()

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return {
        "complaint_id": complaint.id,
        "complaint_text": complaint.complaint_text,
        "location": complaint.location,
        "category": complaint.predicted_category,
        "department": complaint.department,
        "status": complaint.status,
        "photo_path": complaint.photo_path
    }
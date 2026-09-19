from sqlalchemy import Column, Integer, String, Text
from .database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)

    complaint_text = Column(Text, nullable=False)

    location = Column(String, nullable=False)

    predicted_category = Column(String, nullable=False)

    department = Column(String, nullable=False)

    status = Column(String, default="Pending")

    photo_path = Column(String, nullable=True)

    # ---------------- AUTOMATION FIELDS ----------------

    priority = Column(String, nullable=True)

    officer_name = Column(String, nullable=True)

    office_name = Column(String, nullable=True)

    sla_days = Column(Integer, nullable=True)

    due_date = Column(String, nullable=True)

    escalation_level = Column(Integer, default=0)

    summary = Column(Text, nullable=True)
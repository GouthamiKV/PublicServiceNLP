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
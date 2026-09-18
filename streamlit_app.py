import streamlit as st
import os
import shutil

from sqlalchemy.orm import Session

from backend.database import SessionLocal, engine, Base
from backend.model import Complaint
from ml.predict import predict_complaint


# Create database tables
Base.metadata.create_all(bind=engine)

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


st.set_page_config(
    page_title="Public Service App",
    page_icon="🏛️",
    layout="wide"
)


# ---------------- HOME ----------------

def home_page():
    st.title("🏛️ Public Service Complaint System")

    st.subheader("AI-Powered Public Service Complaint Management")

    st.write(
        "Submit public service complaints, automatically classify them "
        "using AI, forward them to the appropriate department, and track "
        "their status."
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    col1.metric("🤖 AI Classification", "Enabled")
    col2.metric("🏢 Department Mapping", "Automatic")
    col3.metric("📊 Complaint Tracking", "Enabled")

    st.divider()

    st.subheader("How the System Works")

    st.write("1️⃣ Citizen submits a complaint")
    st.write("2️⃣ AI predicts the complaint category")
    st.write("3️⃣ System identifies the concerned department")
    st.write("4️⃣ Complaint is stored in the database")
    st.write("5️⃣ Admin updates the complaint status")
    st.write("6️⃣ Citizen tracks the complaint")


# ---------------- SUBMIT COMPLAINT ----------------

def submit_page():
    st.title("📝 Submit a Complaint")

    complaint_text = st.text_area(
        "Complaint Details",
        placeholder="Describe your problem..."
    )

    location = st.text_input(
        "Location",
        placeholder="Enter your area or city"
    )

    photo = st.file_uploader(
        "Upload Photo (Optional)",
        type=["jpg", "jpeg", "png"]
    )

    if st.button("🚀 Submit Complaint", type="primary"):

        if not complaint_text.strip():
            st.error("Please enter complaint details.")
            return

        if not location.strip():
            st.error("Please enter the location.")
            return

        category, confidence = predict_complaint(
            complaint_text
        )

        department = DEPARTMENT_MAP.get(
            category,
            "General Public Services"
        )

        photo_path = None

        if photo is not None:
            safe_filename = os.path.basename(photo.name)

            photo_path = os.path.join(
                UPLOAD_FOLDER,
                safe_filename
            )

            with open(photo_path, "wb") as f:
                f.write(photo.getbuffer())

        db: Session = SessionLocal()

        try:
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

            st.success("✅ Complaint submitted successfully!")

            st.divider()

            col1, col2 = st.columns(2)

            col1.metric(
                "Complaint ID",
                complaint.id
            )

            col2.metric(
                "Status",
                "Pending"
            )

            st.write("### AI Classification")
            st.write(f"**Category:** {category}")
            st.write(f"**Department:** {department}")
            st.write(f"**Confidence:** {confidence}%")

            if photo_path:
                st.write("📷 Photo uploaded successfully.")

        finally:
            db.close()


# ---------------- TRACK COMPLAINT ----------------

def track_page():
    st.title("🔎 Track Complaint")

    complaint_id = st.number_input(
        "Enter Complaint ID",
        min_value=1,
        step=1
    )

    if st.button("🔍 Track Complaint", type="primary"):

        db: Session = SessionLocal()

        try:
            complaint = db.query(Complaint).filter(
                Complaint.id == complaint_id
            ).first()

            if not complaint:
                st.error("Complaint not found.")
                return

            st.success("Complaint found!")

            st.divider()

            st.write(
                f"### Complaint ID: {complaint.id}"
            )

            st.write(
                f"**Complaint:** {complaint.complaint_text}"
            )

            st.write(
                f"**Location:** {complaint.location}"
            )

            st.write(
                f"**Category:** {complaint.predicted_category}"
            )

            st.write(
                f"**Department:** {complaint.department}"
            )

            st.write(
                f"**Status:** {complaint.status}"
            )

            if complaint.photo_path:
                filename = os.path.basename(
                    complaint.photo_path
                )

                image_path = os.path.join(
                    UPLOAD_FOLDER,
                    filename
                )

                if os.path.exists(image_path):
                    st.image(
                        image_path,
                        caption="Uploaded Complaint Photo"
                    )

        finally:
            db.close()


# ---------------- ADMIN DASHBOARD ----------------

def admin_page():
    st.title("👨‍💼 Admin Dashboard")

    db: Session = SessionLocal()

    try:
        complaints = db.query(Complaint).all()

        total = len(complaints)

        pending = sum(
            1 for c in complaints
            if c.status == "Pending"
        )

        in_progress = sum(
            1 for c in complaints
            if c.status == "In Progress"
        )

        resolved = sum(
            1 for c in complaints
            if c.status == "Resolved"
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Complaints", total)
        col2.metric("Pending", pending)
        col3.metric("In Progress", in_progress)
        col4.metric("Resolved", resolved)

        st.divider()

        if not complaints:
            st.info("No complaints available.")
            return

        for complaint in complaints:

            with st.expander(
                f"Complaint #{complaint.id} — "
                f"{complaint.predicted_category}"
            ):

                st.write(
                    f"**Complaint:** {complaint.complaint_text}"
                )

                st.write(
                    f"**Location:** {complaint.location}"
                )

                st.write(
                    f"**Category:** {complaint.predicted_category}"
                )

                st.write(
                    f"**Department:** {complaint.department}"
                )

                st.write(
                    f"**Current Status:** {complaint.status}"
                )

                new_status = st.selectbox(
                    "Update Status",
                    [
                        "Pending",
                        "In Progress",
                        "Resolved"
                    ],
                    index=[
                        "Pending",
                        "In Progress",
                        "Resolved"
                    ].index(complaint.status),
                    key=f"status_{complaint.id}"
                )

                if st.button(
                    "Update Status",
                    key=f"update_{complaint.id}"
                ):

                    complaint.status = new_status

                    db.commit()

                    st.success(
                        f"Complaint #{complaint.id} updated."
                    )

                    st.rerun()

                if complaint.photo_path:

                    filename = os.path.basename(
                        complaint.photo_path
                    )

                    image_path = os.path.join(
                        UPLOAD_FOLDER,
                        filename
                    )

                    if os.path.exists(image_path):
                        st.image(
                            image_path,
                            caption="Complaint Photo"
                        )

    finally:
        db.close()


# ---------------- SIDEBAR ----------------

st.sidebar.title("🏛️ Public Service App")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "📝 Submit Complaint",
        "🔎 Track Complaint",
        "👨‍💼 Admin Dashboard"
    ]
)


if page == "🏠 Home":
    home_page()

elif page == "📝 Submit Complaint":
    submit_page()

elif page == "🔎 Track Complaint":
    track_page()

elif page == "👨‍💼 Admin Dashboard":
    admin_page()
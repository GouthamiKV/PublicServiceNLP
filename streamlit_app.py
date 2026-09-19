import streamlit as st
import os

from sqlalchemy.orm import Session

from backend.database import SessionLocal, engine, Base
from backend.model import Complaint
from ml.predict import predict_complaint

from backend.automation import (
    process_complaint,
    check_overdue_complaint
)


# =========================================================
# DATABASE / UPLOAD SETUP
# =========================================================

Base.metadata.create_all(bind=engine)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# DEPARTMENT MAPPING
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
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Public Service App",
    page_icon="🏛️",
    layout="wide"
)


# =========================================================
# HOME PAGE
# =========================================================

def home_page():

    st.title("🏛️ Public Service Complaint System")

    st.subheader(
        "AI-Powered Public Service Complaint Management"
    )

    st.write(
        "Submit public service complaints, automatically classify them "
        "using AI, forward them to the appropriate department, and track "
        "their status."
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "🤖 AI Classification",
        "Enabled"
    )

    col2.metric(
        "🏢 Department Mapping",
        "Automatic"
    )

    col3.metric(
        "📊 Complaint Tracking",
        "Enabled"
    )

    st.divider()

    st.subheader("How the System Works")

    st.write("1️⃣ Citizen submits a complaint")
    st.write("2️⃣ AI predicts the complaint category")
    st.write("3️⃣ System identifies the concerned department")
    st.write("4️⃣ AI determines complaint priority")
    st.write("5️⃣ System assigns an officer and office")
    st.write("6️⃣ System calculates SLA and due date")
    st.write("7️⃣ Complaint is stored in the database")
    st.write("8️⃣ Admin updates the complaint status")
    st.write("9️⃣ Citizen tracks the complaint")
    st.write("🔟 System automatically checks overdue complaints")


# =========================================================
# SUBMIT COMPLAINT
# =========================================================
# =========================================================
# SUBMIT COMPLAINT
# =========================================================

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

    if st.button(
        "🚀 Submit Complaint",
        type="primary"
    ):

        if not complaint_text.strip():

            st.error(
                "Please enter complaint details."
            )

            return

        if not location.strip():

            st.error(
                "Please enter the location."
            )

            return

        # -------------------------------------------------
        # OPEN DATABASE
        # -------------------------------------------------

        db: Session = SessionLocal()

        try:

            # -------------------------------------------------
            # AI CLASSIFICATION
            # -------------------------------------------------

            category, confidence = predict_complaint(
                complaint_text
            )

            department = DEPARTMENT_MAP.get(
                category,
                "General Public Services"
            )

            # -------------------------------------------------
            # AUTOMATIC PROCESSING
            # -------------------------------------------------

            automation = process_complaint(

                complaint_text=complaint_text,

                category=category,

                department=department,

                location=location,

                db=db
            )

            priority = automation["priority"]

            sla_days = automation["sla_days"]

            due_date = automation["due_date"]

            officer_name = automation["officer_name"]

            office_name = automation["office_name"]

            summary = automation["summary"]

            escalation_level = automation[
                "escalation_level"
            ]

            # -------------------------------------------------
            # PHOTO UPLOAD
            # -------------------------------------------------

            photo_path = None

            if photo is not None:

                safe_filename = os.path.basename(
                    photo.name
                )

                photo_path = os.path.join(
                    UPLOAD_FOLDER,
                    safe_filename
                )

                with open(
                    photo_path,
                    "wb"
                ) as f:

                    f.write(
                        photo.getbuffer()
                    )

            # -------------------------------------------------
            # CREATE COMPLAINT
            # -------------------------------------------------

            complaint = Complaint(

                complaint_text=complaint_text,

                location=location,

                predicted_category=category,

                department=department,

                status="Pending",

                photo_path=photo_path,

                priority=priority,

                officer_name=officer_name,

                office_name=office_name,

                sla_days=sla_days,

                due_date=due_date,

                escalation_level=escalation_level,

                summary=summary
            )

            db.add(
                complaint
            )

            db.commit()

            db.refresh(
                complaint
            )

            # -------------------------------------------------
            # SUCCESS
            # -------------------------------------------------

            st.success(
                "✅ Complaint submitted successfully!"
            )

            st.divider()

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Complaint ID",
                complaint.id
            )

            col2.metric(
                "Priority",
                priority
            )

            col3.metric(
                "Status",
                "Pending"
            )

            # -------------------------------------------------
            # AI CLASSIFICATION
            # -------------------------------------------------

            st.write(
                "### 🤖 AI Classification"
            )

            st.write(
                f"**Category:** {category}"
            )

            st.write(
                f"**Department:** {department}"
            )

            st.write(
                f"**Confidence:** {confidence}%"
            )

            # -------------------------------------------------
            # ASSIGNMENT
            # -------------------------------------------------

            st.write(
                "### ⚙️ Automatic Assignment"
            )

            col1, col2 = st.columns(2)

            col1.write(
                f"**👨‍💼 Assigned Officer:** "
                f"{officer_name}"
            )

            col2.write(
                f"**🏢 Assigned Office:** "
                f"{office_name}"
            )

            # -------------------------------------------------
            # SLA
            # -------------------------------------------------

            st.write(
                "### ⏱️ Service Timeline"
            )

            col1, col2 = st.columns(2)

            col1.write(
                f"**SLA:** {sla_days} day(s)"
            )

            col2.write(
                f"**Due Date:** {due_date}"
            )

            # -------------------------------------------------
            # SUMMARY
            # -------------------------------------------------

            st.write(
                "### 📝 AI Complaint Summary"
            )

            st.info(
                summary
            )

            if photo_path:

                st.write(
                    "📷 Photo uploaded successfully."
                )

        finally:

            db.close()
def track_page():

    st.title("🔎 Track Complaint")

    complaint_id = st.number_input(
        "Enter Complaint ID",
        min_value=1,
        step=1
    )

    if st.button(
        "🔍 Track Complaint",
        type="primary"
    ):

        db: Session = SessionLocal()

        try:

            complaint = db.query(
                Complaint
            ).filter(
                Complaint.id == complaint_id
            ).first()

            if not complaint:

                st.error(
                    "Complaint not found."
                )

                return

            st.success(
                "Complaint found!"
            )

            st.divider()

            st.write(
                f"### Complaint ID: {complaint.id}"
            )

            st.write(
                f"**Complaint:** "
                f"{complaint.complaint_text}"
            )

            st.write(
                f"**Location:** "
                f"{complaint.location}"
            )

            st.write(
                f"**Category:** "
                f"{complaint.predicted_category}"
            )

            st.write(
                f"**Department:** "
                f"{complaint.department}"
            )

            st.write(
                f"**Status:** "
                f"{complaint.status}"
            )

            # -------------------------------------------------
            # AUTOMATION DETAILS
            # -------------------------------------------------

            st.divider()

            st.write(
                "### ⚙️ Complaint Assignment"
            )

            col1, col2 = st.columns(2)

            col1.write(
                f"**Priority:** "
                f"{complaint.priority or 'Not available'}"
            )

            col2.write(
                f"**Assigned Officer:** "
                f"{complaint.officer_name or 'Not assigned'}"
            )

            col1, col2 = st.columns(2)

            col1.write(
                f"**Office:** "
                f"{complaint.office_name or 'Not assigned'}"
            )

            col2.write(
                f"**SLA:** "
                f"{complaint.sla_days or 'Not available'} day(s)"
            )

            st.write(
                f"**Expected Completion:** "
                f"{complaint.due_date or 'Not available'}"
            )

            # -------------------------------------------------
            # ESCALATION STATUS
            # -------------------------------------------------

            escalation_level = (
                complaint.escalation_level or 0
            )

            if escalation_level == 0:

                st.success(
                    "🟢 No escalation"
                )

            elif escalation_level == 1:

                st.warning(
                    "🟡 Overdue — Escalation Level 1"
                )

            elif escalation_level == 2:

                st.warning(
                    "🟠 Escalated — Level 2"
                )

            else:

                st.error(
                    "🔴 Critical Escalation — Level 3"
                )

            # -------------------------------------------------
            # SUMMARY
            # -------------------------------------------------

            if complaint.summary:

                st.write(
                    "### 📝 Complaint Summary"
                )

                st.info(
                    complaint.summary
                )

            # -------------------------------------------------
            # PHOTO
            # -------------------------------------------------

            if complaint.photo_path:

                filename = os.path.basename(
                    complaint.photo_path
                )

                image_path = os.path.join(
                    UPLOAD_FOLDER,
                    filename
                )

                if os.path.exists(
                    image_path
                ):

                    st.image(
                        image_path,
                        caption="Uploaded Complaint Photo"
                    )

        finally:

            db.close()


# =========================================================
# ADMIN DASHBOARD
# =========================================================

def admin_page():

    st.title(
        "👨‍💼 Admin Dashboard"
    )

    db: Session = SessionLocal()

    try:

        complaints = db.query(
            Complaint
        ).all()

        # -------------------------------------------------
        # AUTOMATIC OVERDUE CHECK
        # -------------------------------------------------

        for complaint in complaints:

            new_level = check_overdue_complaint(
                complaint
            )

            current_level = (
                complaint.escalation_level or 0
            )

            if new_level > current_level:

                complaint.escalation_level = new_level

                db.commit()

        # Refresh complaint data

        complaints = db.query(
            Complaint
        ).all()

        # -------------------------------------------------
        # STATISTICS
        # -------------------------------------------------

        total = len(
            complaints
        )

        pending = sum(
            1
            for c in complaints
            if c.status == "Pending"
        )

        in_progress = sum(
            1
            for c in complaints
            if c.status == "In Progress"
        )

        resolved = sum(
            1
            for c in complaints
            if c.status == "Resolved"
        )

        escalated = sum(
            1
            for c in complaints
            if (c.escalation_level or 0) > 0
        )

        # -------------------------------------------------
        # DASHBOARD METRICS
        # -------------------------------------------------

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "Total Complaints",
            total
        )

        col2.metric(
            "Pending",
            pending
        )

        col3.metric(
            "In Progress",
            in_progress
        )

        col4.metric(
            "Resolved",
            resolved
        )

        col5.metric(
            "🚨 Escalated",
            escalated
        )

        st.divider()

        if not complaints:

            st.info(
                "No complaints available."
            )

            return

        # =================================================
        # ANALYTICS
        # =================================================

        st.subheader(
            "📊 Complaint Analytics"
        )

        # -------------------------------------------------
        # CATEGORY DISTRIBUTION
        # -------------------------------------------------

        category_counts = {}

        for complaint in complaints:

            category = (
                complaint.predicted_category
                or "Unknown"
            )

            category_counts[category] = (
                category_counts.get(category, 0) + 1
            )

        st.write(
            "### 📂 Complaints by Category"
        )

        st.bar_chart(
            category_counts
        )

        # -------------------------------------------------
        # PRIORITY DISTRIBUTION
        # -------------------------------------------------

        priority_counts = {}

        for complaint in complaints:

            priority = (
                complaint.priority
                or "Not Available"
            )

            priority_counts[priority] = (
                priority_counts.get(priority, 0) + 1
            )

        st.write(
            "### 🚦 Complaints by Priority"
        )

        priority_order = [
            "High",
            "Medium",
            "Low",
            "Not Available"
        ]

        ordered_priority = {}

        for priority in priority_order:

            if priority in priority_counts:

                ordered_priority[priority] = (
                    priority_counts[priority]
                )

        st.bar_chart(
            ordered_priority
        )

        # -------------------------------------------------
        # STATUS DISTRIBUTION
        # -------------------------------------------------

        status_counts = {}

        for complaint in complaints:

            status = (
                complaint.status
                or "Unknown"
            )

            status_counts[status] = (
                status_counts.get(status, 0) + 1
            )

        st.write(
            "### 📌 Complaints by Status"
        )

        st.bar_chart(
            status_counts
        )

        # -------------------------------------------------
        # DEPARTMENT WORKLOAD
        # -------------------------------------------------

        department_counts = {}

        for complaint in complaints:

            department = (
                complaint.department
                or "Unassigned"
            )

            department_counts[department] = (
                department_counts.get(department, 0) + 1
            )

        st.write(
            "### 🏢 Department Workload"
        )

        st.bar_chart(
            department_counts
        )

        # -------------------------------------------------
        # OFFICER WORKLOAD
        # -------------------------------------------------

        officer_counts = {}

        for complaint in complaints:

            officer = (
                complaint.officer_name
                or "Unassigned"
            )

            officer_counts[officer] = (
                officer_counts.get(officer, 0) + 1
            )

        st.write(
            "### 👨‍💼 Officer Workload"
        )

        st.bar_chart(
            officer_counts
        )

        # -------------------------------------------------
        # ESCALATION OVERVIEW
        # -------------------------------------------------

        escalation_counts = {
            "No Escalation": 0,
            "Level 1": 0,
            "Level 2": 0,
            "Level 3": 0
        }

        for complaint in complaints:

            level = (
                complaint.escalation_level or 0
            )

            if level == 0:

                escalation_counts[
                    "No Escalation"
                ] += 1

            elif level == 1:

                escalation_counts[
                    "Level 1"
                ] += 1

            elif level == 2:

                escalation_counts[
                    "Level 2"
                ] += 1

            else:

                escalation_counts[
                    "Level 3"
                ] += 1

        st.write(
            "### 🚨 Escalation Overview"
        )

        st.bar_chart(
            escalation_counts
        )

        st.divider()

        # =================================================
        # COMPLAINT LIST
        # =================================================

        st.subheader(
            "📋 Complaint Management"
        )

        for complaint in complaints:

            with st.expander(

                f"Complaint #{complaint.id} — "
                f"{complaint.predicted_category}"
            ):

                # -----------------------------------------
                # BASIC INFORMATION
                # -----------------------------------------

                st.write(
                    f"**Complaint:** "
                    f"{complaint.complaint_text}"
                )

                st.write(
                    f"**Location:** "
                    f"{complaint.location}"
                )

                st.write(
                    f"**Category:** "
                    f"{complaint.predicted_category}"
                )

                st.write(
                    f"**Department:** "
                    f"{complaint.department}"
                )

                # -----------------------------------------
                # AUTOMATION INFORMATION
                # -----------------------------------------

                st.divider()

                st.write(
                    "### ⚙️ Automatic Processing"
                )

                col1, col2 = st.columns(2)

                col1.write(
                    f"**Priority:** "
                    f"{complaint.priority or 'Not available'}"
                )

                col2.write(
                    f"**Officer:** "
                    f"{complaint.officer_name or 'Not assigned'}"
                )

                col1, col2 = st.columns(2)

                col1.write(
                    f"**Office:** "
                    f"{complaint.office_name or 'Not assigned'}"
                )

                col2.write(
                    f"**SLA:** "
                    f"{complaint.sla_days or 'Not available'} day(s)"
                )

                st.write(
                    f"**Due Date:** "
                    f"{complaint.due_date or 'Not available'}"
                )

                # -----------------------------------------
                # ESCALATION
                # -----------------------------------------

                escalation_level = (
                    complaint.escalation_level or 0
                )

                if escalation_level == 0:

                    st.success(
                        "🟢 No escalation"
                    )

                elif escalation_level == 1:

                    st.warning(
                        "🟡 Overdue — Escalation Level 1"
                    )

                elif escalation_level == 2:

                    st.warning(
                        "🟠 Escalated — Level 2"
                    )

                else:

                    st.error(
                        "🔴 Critical Escalation — Level 3"
                    )

                # -----------------------------------------
                # AI SUMMARY
                # -----------------------------------------

                if complaint.summary:

                    st.write(
                        "### 📝 AI Summary"
                    )

                    st.info(
                        complaint.summary
                    )

                # -----------------------------------------
                # CURRENT STATUS
                # -----------------------------------------

                st.write(
                    f"**Current Status:** "
                    f"{complaint.status}"
                )

                # -----------------------------------------
                # STATUS UPDATE
                # -----------------------------------------

                status_options = [
                    "Pending",
                    "In Progress",
                    "Resolved"
                ]

                current_status = (
                    complaint.status
                    if complaint.status
                    in status_options
                    else "Pending"
                )

                new_status = st.selectbox(

                    "Update Status",

                    status_options,

                    index=status_options.index(
                        current_status
                    ),

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

                # -----------------------------------------
                # PHOTO
                # -----------------------------------------

                if complaint.photo_path:

                    filename = os.path.basename(
                        complaint.photo_path
                    )

                    image_path = os.path.join(
                        UPLOAD_FOLDER,
                        filename
                    )

                    if os.path.exists(
                        image_path
                    ):

                        st.image(
                            image_path,
                            caption="Complaint Photo"
                        )

    finally:

        db.close()
        # =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "🏛️ Public Service App"
)

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "📝 Submit Complaint",
        "🔎 Track Complaint",
        "👨‍💼 Admin Dashboard"
    ]
)


# =========================================================
# PAGE ROUTING
# =========================================================

if page == "🏠 Home":

    home_page()

elif page == "📝 Submit Complaint":

    submit_page()

elif page == "🔎 Track Complaint":

    track_page()

elif page == "👨‍💼 Admin Dashboard":

    admin_page()
from datetime import datetime, timedelta


# =========================================================
# DEMO OFFICER DATA
# =========================================================
# These are project/demo officers.
# They can be replaced with real staff data later.

OFFICERS = [
    {
        "name": "Ananya Sharma",
        "department": "Municipal Sanitation Department",
        "office": "Central Municipal Office",
        "area": "Central",
    },
    {
        "name": "Rahul Kumar",
        "department": "Municipal Sanitation Department",
        "office": "East Municipal Office",
        "area": "East",
    },
    {
        "name": "Priya Nair",
        "department": "Electrical / Municipal Department",
        "office": "Central Electrical Office",
        "area": "Central",
    },
    {
        "name": "Arjun Reddy",
        "department": "Water Supply Department",
        "office": "East Water Supply Office",
        "area": "East",
    },
    {
        "name": "Sneha Rao",
        "department": "Citizen Services Department",
        "office": "Central Citizen Service Centre",
        "area": "Central",
    },
    {
        "name": "Vikram Singh",
        "department": "Electricity Department",
        "office": "Central Electricity Office",
        "area": "Central",
    },
    {
        "name": "Meera Joshi",
        "department": "Social Welfare Department",
        "office": "Central Social Welfare Office",
        "area": "Central",
    },
    {
        "name": "Kiran Patel",
        "department": "Public Health Department",
        "office": "Central Public Health Office",
        "area": "Central",
    },
    {
        "name": "Neha Verma",
        "department": "Transport Department",
        "office": "Central Transport Office",
        "area": "Central",
    },
    {
        "name": "Rohit Das",
        "department": "Public Works Department",
        "office": "East Public Works Office",
        "area": "East",
    },
    {
        "name": "Divya Menon",
        "department": "Municipal Drainage Department",
        "office": "East Drainage Office",
        "area": "East",
    },
]


# =========================================================
# SLA RULES
# =========================================================
# These are configurable project/demo values.
# They are NOT official government service standards.

SLA_DAYS = {
    "Sanitation": 3,
    "Street Lighting": 5,
    "Certificates": 7,
    "Water Supply": 3,
    "Electricity": 2,
    "Welfare Scheme": 7,
    "Public Health": 2,
    "Public Transport": 5,
    "Road Damage": 7,
    "Drainage": 4,
}


# =========================================================
# PRIORITY
# =========================================================

def calculate_priority(complaint_text, category):

    text = complaint_text.lower()

    high_keywords = [
        "emergency",
        "danger",
        "dangerous",
        "accident",
        "fire",
        "flood",
        "leak",
        "burst",
        "electric shock",
        "shock",
        "hospital",
        "injury",
        "life threatening",
        "sewage overflow",
        "major damage",
        "road blocked",
        "fallen pole",
        "fallen tree",
    ]

    medium_keywords = [
        "urgent",
        "not working",
        "broken",
        "damaged",
        "overflow",
        "shortage",
        "no water",
        "no electricity",
        "dark",
        "garbage",
        "waste",
        "pothole",
    ]

    for keyword in high_keywords:

        if keyword in text:
            return "High"

    for keyword in medium_keywords:

        if keyword in text:
            return "Medium"

    if category in [
        "Public Health",
        "Electricity",
        "Water Supply"
    ]:
        return "Medium"

    return "Low"


# =========================================================
# SLA CALCULATION
# =========================================================

def calculate_sla(category, priority):

    base_days = SLA_DAYS.get(
        category,
        7
    )

    if priority == "High":

        return max(
            1,
            base_days - 1
        )

    if priority == "Medium":

        return base_days

    return base_days + 2


# =========================================================
# DUE DATE
# =========================================================

def calculate_due_date(sla_days):

    due_date = (
        datetime.now()
        + timedelta(days=sla_days)
    )

    return due_date.strftime(
        "%Y-%m-%d"
    )


# =========================================================
# AREA DETECTION
# =========================================================

def detect_area(location):

    text = location.lower()

    east_keywords = [
        "whitefield",
        "marathahalli",
        "kr puram",
        "hoodi",
        "mahadevapura",
        "ramamurthy nagar",
        "bellandur",
    ]

    central_keywords = [
        "mg road",
        "majestic",
        "shivajinagar",
        "indiranagar",
        "koramangala",
        "richmond",
        "central",
    ]

    for keyword in east_keywords:

        if keyword in text:
            return "East"

    for keyword in central_keywords:

        if keyword in text:
            return "Central"

    return "Central"


# =========================================================
# OFFICER WORKLOAD
# =========================================================

def get_officer_workload(db, officer_name):

    """
    Counts active complaints assigned to an officer.

    Resolved complaints are not counted because
    they no longer contribute to active workload.
    """

    if db is None:
        return 0

    try:

        from backend.model import Complaint

        count = db.query(
            Complaint
        ).filter(
            Complaint.officer_name == officer_name,
            Complaint.status != "Resolved"
        ).count()

        return count

    except Exception:

        return 0


# =========================================================
# OFFICER ASSIGNMENT
# =========================================================

def assign_officer(
    department,
    location,
    db=None
):

    """
    Automatically selects an officer using:

    1. Department
    2. Area
    3. Current active workload

    The officer with the lowest active workload
    in the relevant area is selected.
    """

    area = detect_area(
        location
    )

    matching_officers = [

        officer

        for officer in OFFICERS

        if officer["department"] == department
    ]

    if not matching_officers:

        return (
            "Unassigned Officer",
            "General Public Services Office"
        )

    # Prefer officers serving the detected area
    area_matches = [

        officer

        for officer in matching_officers

        if officer["area"] == area
    ]

    if area_matches:

        candidates = area_matches

    else:

        candidates = matching_officers

    # -----------------------------------------------------
    # WORKLOAD BALANCING
    # -----------------------------------------------------

    if db is not None:

        selected = min(
            candidates,
            key=lambda officer:
                get_officer_workload(
                    db,
                    officer["name"]
                )
        )

    else:

        # Fallback for calls that don't provide a database
        selected = candidates[0]

    return (
        selected["name"],
        selected["office"]
    )


# =========================================================
# COMPLAINT SUMMARY
# =========================================================

def generate_summary(
    complaint_text,
    category
):

    text = complaint_text.strip()

    if len(text) <= 120:

        return (
            f"{category} complaint: {text}"
        )

    shortened = (
        text[:117]
        .rsplit(" ", 1)[0]
    )

    return (
        f"{category} complaint: "
        f"{shortened}..."
    )


# =========================================================
# COMPLETE AUTOMATION
# =========================================================

def process_complaint(
    complaint_text,
    category,
    department,
    location,
    db=None
):

    """
    Runs all automatic complaint processing.

    db is optional so the function remains compatible
    with existing code.
    """

    priority = calculate_priority(
        complaint_text,
        category
    )

    sla_days = calculate_sla(
        category,
        priority
    )

    due_date = calculate_due_date(
        sla_days
    )

    officer_name, office_name = assign_officer(
        department,
        location,
        db
    )

    summary = generate_summary(
        complaint_text,
        category
    )

    return {
        "priority": priority,

        "sla_days": sla_days,

        "due_date": due_date,

        "officer_name": officer_name,

        "office_name": office_name,

        "summary": summary,

        "escalation_level": 0,
    }


# =========================================================
# OVERDUE / ESCALATION CHECK
# =========================================================

def check_overdue_complaint(complaint):

    """
    Checks whether a complaint has passed its due date.

    Resolved complaints are never escalated.
    """

    if complaint.status == "Resolved":

        return (
            complaint.escalation_level or 0
        )

    if not complaint.due_date:

        return (
            complaint.escalation_level or 0
        )

    try:

        due_date = datetime.strptime(
            complaint.due_date,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        return (
            complaint.escalation_level or 0
        )

    today = datetime.now().date()

    if today > due_date:

        current_level = (
            complaint.escalation_level or 0
        )

        new_level = current_level + 1

        return min(
            new_level,
            3
        )

    return (
        complaint.escalation_level or 0
    )
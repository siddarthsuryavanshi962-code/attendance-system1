import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

from firebase_handler import read_csv, upload_csv

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Attendance System", layout="wide")

# ================= LOGIN =================
USERS = {
    "hod": {"password": "hod123", "role": "HOD"},
    "tech": {"password": "tech123", "role": "TEACHER"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("Attendance Login")

    with st.form("login"):
        uid = st.text_input("User ID")
        pwd = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit and uid in USERS and USERS[uid]["password"] == pwd:
        st.session_state.logged_in = True
        st.session_state.role = USERS[uid]["role"]
        st.rerun()
    elif submit:
        st.error("Invalid credentials")

    st.stop()

# ================= SIDEBAR =================
page = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Upload Students CSV", "Upload PDF / Image"]
)

year = "BE" if st.session_state.role == "TEACHER" else st.sidebar.selectbox(
    "Select Year", ["SE", "TE", "BE"]
)

mode = st.sidebar.radio("Mode", ["Day-wise", "Lecture-wise"])

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

# =================================================
# ============ UPLOAD STUDENTS CSV =================
# =================================================
if page == "Upload Students CSV":

    st.title("⬆️ Upload Students CSV")

    st.info("CSV must contain columns: Name, RollNo, Class")

    uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        st.subheader("Preview")
        st.dataframe(df, use_container_width=True)

        if st.button("✅ Upload to Firebase"):
            path = f"students/students_{year}.csv"
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            upload_csv(io.BytesIO(csv_bytes), path)
            st.success(f"Students uploaded successfully to {path}")

    st.stop()

# =================================================
# ============ UPLOAD PDF / IMAGE ==================
# =================================================
if page == "Upload PDF / Image":

    st.title("📤 Upload PDF / Image")

    st.info("Upload attendance sheets, roll-call PDFs, or signed images")

    uploaded_file = st.file_uploader(
        "Choose file",
        type=["pdf", "jpg", "jpeg", "png"]
    )

    if uploaded_file:
        st.write("File name:", uploaded_file.name)
        st.write("File type:", uploaded_file.type)

        if st.button("✅ Upload to Firebase"):
            path = f"documents/{year}/{uploaded_file.name}"
            upload_csv(uploaded_file, path)
            st.success(f"File uploaded successfully to {path}")

    st.stop()

# =================================================
# ================= DASHBOARD =====================
# =================================================
st.title("Student Attendance")

att = read_csv(f"attendance/attendance_{year}.csv")
tt = read_csv(f"timetable/{year}_timetable.csv")

if att is None or tt is None:
    st.error("CSV missing")
    st.stop()

# ================= CLEAN DATA =================
att.columns = att.columns.str.lower().str.strip()
tt.columns = tt.columns.str.lower().str.strip()

roll_col = next(c for c in att.columns if "roll" in c)
name_col = next(c for c in att.columns if "name" in c)
time_col = next(c for c in att.columns if "time" in c or "date" in c)

att["datetime"] = pd.to_datetime(att[time_col], errors="coerce")
att["date"] = att["datetime"].dt.date
att["time"] = att["datetime"].dt.time

tt["start"] = pd.to_datetime(tt["start"], format="%H:%M").dt.time
tt["end"] = pd.to_datetime(tt["end"], format="%H:%M").dt.time

# =================================================
# DAY-WISE
# =================================================
if mode == "Day-wise":

    daily = att.drop_duplicates(subset=[roll_col, "date"])

    present = (
        daily
        .groupby([roll_col, name_col])
        .size()
        .reset_index(name="Present Days")
    )

    total_days = att["date"].nunique()
    present["Attendance %"] = (present["Present Days"] / total_days) * 100

    labels = present[name_col] + " (" + present[roll_col].astype(str) + ")"
    x = range(len(present))

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(x, present["Attendance %"], width=0.3)

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=15)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Attendance %")

    st.pyplot(fig, use_container_width=True)
    st.dataframe(present)

    csv = present.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Day-wise Attendance",
        csv,
        f"{year}_daywise_attendance.csv",
        "text/csv"
    )

# =================================================
# LECTURE-WISE
# =================================================
else:

    students = att[[roll_col, name_col]].drop_duplicates()
    students["label"] = students[name_col] + " (" + students[roll_col].astype(str) + ")"

    sel = st.selectbox("Select Student", students["label"])
    match = students.loc[students["label"] == sel]

    if match.empty:
        st.warning("No attendance data found for this student yet")
        st.stop()

    roll = match[roll_col].iloc[0]
    student_att = att[att[roll_col] == roll]

    records = []

    for _, r in student_att.iterrows():
        for _, t in tt.iterrows():
            if t["start"] <= r["time"] <= t["end"]:
                records.append(t["subject"])

    if not records:
        st.warning("No lectures matched")
        st.stop()

    lec = pd.Series(records).value_counts().reset_index()
    lec.columns = ["Subject", "Lectures"]

    x = list(range(len(lec)))

    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(x, lec["Lectures"], width=0.12)

    if len(lec) == 1:
        ax.set_xlim(-0.5, 0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(lec["Subject"], rotation=10)
    ax.set_ylabel("Lectures")

    st.pyplot(fig, use_container_width=False)
    st.dataframe(lec)

    csv = lec.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Lecture-wise Attendance",
        csv,
        f"{year}_lecturewise_attendance.csv",
        "text/csv"
    )

import pandas as pd

def merge_attendance_timetable(att, tt):
    att["Time"] = pd.to_datetime(att["Time"])
    tt["Start"] = pd.to_datetime(tt["Start"])
    tt["End"] = pd.to_datetime(tt["End"])

    subjects = []

    for _, row in att.iterrows():
        subject = tt[
            (tt["Start"].dt.time <= row["Time"].dt.time) &
            (tt["End"].dt.time >= row["Time"].dt.time)
        ]["Subject"]

        subjects.append(subject.iloc[0] if not subject.empty else "Unknown")

    att["Subject"] = subjects
    return att

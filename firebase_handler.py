import firebase_admin
from firebase_admin import credentials, storage
import streamlit as st
import pandas as pd
import tempfile
import os

# =====================================================
# 🔥 FIREBASE INITIALIZATION (Using Streamlit Secrets)
# =====================================================

if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(
        cred,
        {
           "storageBucket": st.secrets["firebase"]["faceattendance-8429c.firebasestorage.app"]

        },
    )

bucket = storage.bucket()

# =====================================================
# 📥 READ CSV FROM FIREBASE STORAGE
# =====================================================

def read_csv(path):
    """
    Reads CSV file from Firebase Storage.
    Returns pandas DataFrame or None if not exists.
    """

    blob = bucket.blob(path)

    if not blob.exists():
        return None

    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        blob.download_to_filename(temp_file.name)

        df = pd.read_csv(temp_file.name)

        temp_file.close()
        os.unlink(temp_file.name)

        return df

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


# =====================================================
# 📤 UPLOAD CSV TO FIREBASE STORAGE
# =====================================================

def upload_csv(file_bytes, path):
    """
    Uploads CSV to Firebase Storage.
    file_bytes must be BytesIO object.
    """

    try:
        blob = bucket.blob(path)
        blob.upload_from_file(file_bytes, content_type="text/csv")
        blob.make_public()  # Optional (remove if not needed)

        return True

    except Exception as e:
        st.error(f"Error uploading file: {e}")
        return False

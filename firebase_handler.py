import streamlit as st
import pandas as pd
import io

import firebase_admin
from firebase_admin import credentials, storage

# ================= INIT FIREBASE =================
if not firebase_admin._apps:
    firebase_creds = {
        "type": st.secrets["firebase"]["type"],
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        "private_key": st.secrets["firebase"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["firebase"]["client_email"],
        "client_id": st.secrets["firebase"]["client_id"],
        "auth_uri": st.secrets["firebase"]["auth_uri"],
        "token_uri": st.secrets["firebase"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
    }

    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(
        cred,
        {"storageBucket": st.secrets["firebase"]["storageBucket"]}
    )

bucket = storage.bucket()

# ================= FUNCTIONS =================
def upload_csv(file_bytes, path):
    blob = bucket.blob(path)
    blob.upload_from_file(file_bytes, content_type="text/csv")

def read_csv(path):
    try:
        blob = bucket.blob(path)
        if not blob.exists():
            return None
        data = blob.download_as_bytes()
        return pd.read_csv(io.BytesIO(data))
    except Exception:
        return None

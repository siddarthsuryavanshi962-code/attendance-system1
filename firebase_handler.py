import firebase_admin
from firebase_admin import credentials, storage
import firebase_admin
import os

# ===============================
# LOCAL FIREBASE INITIALIZATION
# ===============================

if not firebase_admin._apps:

    cred = credentials.Certificate("firebase_key.json")  # <-- keep this file in same folder

    firebase_admin.initialize_app(cred, {
        'storageBucket': 'faceattendance-8429c.firebasestorage.app'  # replace with your bucket name
    })

bucket = storage.bucket()


# ===============================
# READ CSV FROM FIREBASE STORAGE
# ===============================
def read_csv(path):
    try:
        blob = bucket.blob(path)
        data = blob.download_as_bytes()
        import pandas as pd
        from io import BytesIO
        return pd.read_csv(BytesIO(data))
    except:
        return None


# ===============================
# UPLOAD CSV TO FIREBASE STORAGE
# ===============================
def upload_csv(file_bytes, path):
    blob = bucket.blob(path)
    blob.upload_from_file(file_bytes, content_type="text/csv")

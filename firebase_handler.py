import firebase_admin
from firebase_admin import credentials, storage
import pandas as pd
import tempfile

cred = credentials.Certificate("firebase_key.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        "storageBucket": "faceattendance-8429c.firebasestorage.app"
    })

bucket = storage.bucket()

def read_csv(path):
    blob = bucket.blob(path)
    if not blob.exists():
        return None

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        blob.download_to_filename(tmp.name)
        return pd.read_csv(tmp.name)

def upload_csv(file, path):
    blob = bucket.blob(path)
    blob.upload_from_file(file)

# ✅ ADD THIS FUNCTION
def file_exists(path):
    return bucket.blob(path).exists()

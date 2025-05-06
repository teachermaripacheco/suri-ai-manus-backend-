import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json # Added for parsing JSON string from env var

# Load environment variables from .env file (primarily for local development)
load_dotenv()

# --- Firebase Admin SDK Initialization ---
try:
    firebase_service_account_json_str = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_JSON")
    if firebase_service_account_json_str:
        # Load from environment variable (for Railway)
        service_account_info = json.loads(firebase_service_account_json_str)
        cred = credentials.Certificate(service_account_info)
        print("Initializing Firebase Admin SDK from environment variable.")
    else:
        # Load from local file (for local development)
        cred_path = os.path.join(os.path.dirname(__file__), "..", "firebase-service-account-key.json")
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"Firebase service account key file not found at {cred_path} and FIREBASE_SERVICE_ACCOUNT_KEY_JSON env var is not set.")
        cred = credentials.Certificate(cred_path)
        print("Initializing Firebase Admin SDK from local file.")

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully.")
    else:
        print("Firebase Admin SDK already initialized.")
    db = firestore.client() # Firestore client instance
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    db = None # Set db to None if initialization fails
# --- End Firebase Initialization ---

# Import route modules
from .routes import auth as auth_router
from .routes import student as student_router
from .routes import admin as admin_router

app = FastAPI(title="SURI AI Backend", version="0.1.0")

# CORS Configuration
# Allow all origins for now, can be restricted later
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000") # Default for local dev
origins = [
    frontend_url,
    "http://localhost:3000",
    "http://localhost:3001", # In case port 3000 is busy
    "http://localhost:5173",
    "http://localhost:5174",
]
# Remove duplicates and empty strings if FRONTEND_URL is one of the defaults
origins = list(set(filter(None, origins)))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the SURI AI Backend"}

# Include routers from route modules
app.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
app.include_router(student_router.router, prefix="/student", tags=["Student"])
app.include_router(admin_router.router, prefix="/admin", tags=["Admin"])


# Note: Uvicorn will run this app instance.
# For Railway, the Procfile will handle the port using $PORT
# Example local command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


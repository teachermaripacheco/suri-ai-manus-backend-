from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import firebase_admin
from firebase_admin import auth as firebase_auth
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- TODO: Move these to a config file or environment variables --- 
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_please_change_me") # CHANGE THIS!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# --- End Config ---

# Import models (adjust path if needed)
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from models.user import UserCreate, UserPublic, Token, TokenData

router = APIRouter()

# --- Firebase Authentication Functions ---

def create_firebase_user(user_data: UserCreate):
    try:
        user_record = firebase_auth.create_user(
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.name,
            email_verified=False # Or True if you implement verification
        )
        # You might want to store additional user info (like name) in Firestore
        # using user_record.uid as the document ID.
        # db.collection("users").document(user_record.uid).set({"name": user_data.name, "email": user_data.email})
        return {"id": user_record.uid, "email": user_record.email, "name": user_record.display_name}
    except firebase_auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Email already registered")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firebase user creation failed: {e}")

def authenticate_firebase_user(email: str, password: str):
    """Authenticates user with Firebase Auth (requires client-side handling or custom token)
       Note: Firebase Admin SDK cannot directly verify passwords.
       This function is a placeholder concept. Proper flow involves:
       1. Client signs in with Firebase SDK (JS, Android, iOS).
       2. Client gets an ID token.
       3. Client sends ID token to backend.
       4. Backend verifies ID token using firebase_auth.verify_id_token().
       For a pure backend password check, you might need a custom system or different auth provider.
       Here, we simulate getting user info after *assuming* client-side auth was successful.
    """
    try:
        user_record = firebase_auth.get_user_by_email(email)
        # We CANNOT verify the password here with Admin SDK.
        # Returning user info assuming password check happened client-side or is bypassed for now.
        return {"id": user_record.uid, "email": user_record.email, "name": user_record.display_name}
    except firebase_auth.UserNotFoundError:
        return None
    except Exception as e:
        print(f"Error fetching user by email: {e}") # Log error
        return None

# --- JWT Token Functions (If not using Firebase ID tokens directly) ---

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15) # Default expiry
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Routes ---

@router.post("/register", response_model=UserPublic)
async def register_user(user: UserCreate):
    """Registers a new user using Firebase Authentication."""
    created_user = create_firebase_user(user)
    return created_user

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Logs in a user (simulated) and returns a JWT access token.
    IMPORTANT: This route bypasses actual password verification due to Firebase Admin SDK limitations.
    In a real app, the client should send a Firebase ID Token instead of username/password.
    The backend would then verify the ID token.
    """
    user = authenticate_firebase_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password (simulation - password not checked)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create a JWT token containing user info (e.g., email or Firebase UID)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "uid": user["id"] }, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Dependency for getting current user from JWT token ---
# This would replace fake_get_current_user

from fastapi.security import OAuth2PasswordBearer
from datetime import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        uid: str | None = payload.get("uid")
        if email is None or uid is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # You might want to fetch the user from Firebase Auth again to ensure they still exist
    # user = firebase_auth.get_user(uid)
    # if user is None:
    #     raise credentials_exception
    
    # Return user info extracted from token (or fetched from Firebase)
    return {"id": uid, "email": email} # Or return the full user object if fetched

async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    # Placeholder: In a real app, check if current_user["id"] has admin role in Firestore/DB
    # For now, assume the first registered user or a specific UID is admin
    # Example: if current_user["id"] != "EXPECTED_ADMIN_UID":
    #     raise HTTPException(status_code=403, detail="Not an admin")
    print(f"Admin access attempt by: {current_user['email']}") # Logging
    return current_user



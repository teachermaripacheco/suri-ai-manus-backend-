from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore, auth as firebase_auth

# Import models and auth dependency
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from models.user import UserPublic # Assuming UserPublic is suitable for listing
from .auth import get_current_admin_user # Use the JWT-based admin dependency

# Get Firestore client (initialized in main.py)
try:
    db = firestore.client()
    # Assuming you might store user details beyond Firebase Auth in a 'users' collection
    users_collection = db.collection("users") 
    # References to other collections needed for detailed view
    inputs_collection = db.collection("student_inputs")
    plans_collection = db.collection("student_plans")
    feedback_collection = db.collection("student_feedback")
except Exception as e:
    print(f"Error getting Firestore client in admin.py: {e}")
    db = None

router = APIRouter()

@router.get("/users", response_model=list[UserPublic]) # Use UserPublic or a dedicated AdminUserView
async def read_users(current_admin: dict = Depends(get_current_admin_user)):
    """Retrieves a list of all users from Firebase Authentication (admin only)."""
    if not db:
        raise HTTPException(status_code=500, detail="Firestore client not initialized")
        
    users_list = []
    try:
        # Iterate through all users in Firebase Auth
        for user_record in firebase_auth.list_users().iterate_all():
            # Optionally fetch additional details from Firestore 'users' collection if needed
            # user_details_doc = users_collection.document(user_record.uid).get()
            # user_details = user_details_doc.to_dict() if user_details_doc.exists else {}
            users_list.append(
                UserPublic(
                    id=user_record.uid,
                    email=user_record.email,
                    name=user_record.display_name or "N/A" # Use display_name from Auth
                    # Add other fields from Firestore if fetched
                )
            )
        return users_list
    except Exception as e:
        print(f"Error listing users from Firebase Auth: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {e}")

@router.get("/users/{user_id}", response_model=dict) # Using dict for flexibility in detailed view
async def read_user_details(user_id: str, current_admin: dict = Depends(get_current_admin_user)):
    """Retrieves detailed information for a specific user from Firebase Auth and Firestore (admin only)."""
    if not db:
        raise HTTPException(status_code=500, detail="Firestore client not initialized")

    try:
        # 1. Get basic user info from Firebase Auth
        user_record = firebase_auth.get_user(user_id)
        user_details = {
            "id": user_record.uid,
            "email": user_record.email,
            "name": user_record.display_name or "N/A",
            "registrationDate": user_record.user_metadata.creation_timestamp, # Timestamp might need formatting
            "emailVerified": user_record.email_verified,
            # Initialize other fields
            "goals": [],
            "struggles": "",
            "latestPlan": None,
            "feedbackHistory": []
        }

        # 2. Get latest student input from Firestore
        input_query = inputs_collection.where("user_id", "==", user_id).order_by("created_at", direction=firestore.Query.DESCENDING).limit(1)
        input_docs = input_query.stream()
        for doc in input_docs:
            input_data = doc.to_dict()
            user_details["goals"] = input_data.get("goals", [])
            user_details["struggles"] = input_data.get("struggles", "")
            break

        # 3. Get latest plan from Firestore
        plan_query = plans_collection.where("user_id", "==", user_id).order_by("created_at", direction=firestore.Query.DESCENDING).limit(1)
        plan_docs = plan_query.stream()
        for doc in plan_docs:
            plan_data = doc.to_dict()
            user_details["latestPlan"] = {"id": doc.id, "week": plan_data.get("week"), "theme": plan_data.get("theme")}
            user_details["planStatus"] = "Active" # Assuming plan exists means active
            break
        else: # If no plan found
             user_details["planStatus"] = "Pending Input" # Or determine based on input existence

        # 4. Get feedback history from Firestore (limit for brevity)
        feedback_query = feedback_collection.where("user_id", "==", user_id).order_by("created_at", direction=firestore.Query.DESCENDING).limit(5)
        feedback_docs = feedback_query.stream()
        for doc in feedback_docs:
            feedback_data = doc.to_dict()
            user_details["feedbackHistory"].append({
                "id": doc.id,
                "plan_id": feedback_data.get("plan_id"),
                "rating": feedback_data.get("rating"),
                "comments": feedback_data.get("comments", ""),
                "created_at": feedback_data.get("created_at") # Timestamp might need formatting
            })
            # Update last feedback rating if needed for summary view (though maybe redundant here)
            if user_details.get("lastFeedbackRating") is None:
                 user_details["lastFeedbackRating"] = feedback_data.get("rating")

        return user_details

    except firebase_auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found in Firebase Authentication")
    except Exception as e:
        print(f"Error fetching user details for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user details: {e}")



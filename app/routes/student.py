from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore
import datetime

# Import models and auth dependency
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from models.student import StudentInputCreate, PlanCreate, FeedbackCreate, PlanInDB, FeedbackInDB, StudentInputInDB
from .auth import get_current_user # Use the JWT-based dependency

# Get Firestore client (initialized in main.py)
# This assumes main.py runs first and initializes db
try:
    db = firestore.client()
    inputs_collection = db.collection("student_inputs")
    plans_collection = db.collection("student_plans")
    feedback_collection = db.collection("student_feedback")
except Exception as e:
    print(f"Error getting Firestore client in student.py: {e}")
    db = None # Handle case where Firebase might not be initialized

router = APIRouter()

@router.post("/input", response_model=StudentInputInDB)
async def submit_student_input(input_data: StudentInputCreate, current_user: dict = Depends(get_current_user)):
    """Receives student goals and struggles and saves to Firestore."""
    if not db:
        raise HTTPException(status_code=500, detail="Firestore client not initialized")
        
    user_id = current_user["id"]
    timestamp = datetime.datetime.utcnow()
    
    input_doc_data = input_data.dict()
    input_doc_data["user_id"] = user_id
    input_doc_data["created_at"] = timestamp
    
    try:
        # Add a new document with an auto-generated ID
        update_time, doc_ref = inputs_collection.add(input_doc_data)
        print(f"Student input saved for user {user_id} with doc ID: {doc_ref.id}")
        
        # Prepare response model
        response_data = input_doc_data.copy()
        response_data["id"] = doc_ref.id
        return StudentInputInDB(**response_data)
        
    except Exception as e:
        print(f"Error saving student input to Firestore: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save student input: {e}")

@router.post("/plan", response_model=PlanInDB)
async def trigger_plan_generation(current_user: dict = Depends(get_current_user)):
    """Triggers the AI plan generation (mock) and saves the plan to Firestore."""
    if not db:
        raise HTTPException(status_code=500, detail="Firestore client not initialized")
        
    user_id = current_user["id"]
    timestamp = datetime.datetime.utcnow()

    # --- TODO: Replace with actual AI Plan Generation Logic --- 
    # This should ideally fetch the latest student input for the user_id
    # and call the AI service.
    # For now, we generate a mock plan.
    mock_plan_data = {
        "user_id": user_id,
        "week": 1,
        "theme": "Mock: Introduction & Basic Greetings (Firestore)",
        "goals": [
            "Learn mock greetings via Firestore",
            "Introduce yourself (mock, Firestore)",
        ],
        "activities": [
            { "type": "Lesson", "title": "Mock Video (FS)", "duration": "15 mins" },
            { "type": "Practice", "title": "Mock Flashcards (FS)", "duration": "10 mins" },
        ],
        "focusAreas": ["Mock Pronunciation (FS)", "Mock Vocabulary (FS)"],
        "created_at": timestamp
    }
    # --- End AI Plan Generation Placeholder ---
    
    try:
        # Add the generated plan to Firestore
        update_time, doc_ref = plans_collection.add(mock_plan_data)
        print(f"Plan generated and saved for user {user_id} with doc ID: {doc_ref.id}")
        
        # Prepare response model
        response_data = mock_plan_data.copy()
        response_data["id"] = doc_ref.id
        return PlanInDB(**response_data)
        
    except Exception as e:
        print(f"Error saving plan to Firestore: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save generated plan: {e}")

@router.get("/plan", response_model=PlanInDB)
async def get_student_plan(current_user: dict = Depends(get_current_user)):
    """Retrieves the latest learning plan for the user from Firestore."""
    if not db:
        raise HTTPException(status_code=500, detail="Firestore client not initialized")
        
    user_id = current_user["id"]
    
    try:
        # Query for plans for the user, order by creation time descending, limit to 1
        query = plans_collection.where("user_id", "==", user_id).order_by("created_at", direction=firestore.Query.DESCENDING).limit(1)
        results = query.stream()
        
        latest_plan = None
        for doc in results:
            plan_data = doc.to_dict()
            plan_data["id"] = doc.id
            latest_plan = PlanInDB(**plan_data)
            break # Since we limited to 1
            
        if not latest_plan:
            raise HTTPException(status_code=404, detail="Plan not found for user")
            
        return latest_plan
        
    except Exception as e:
        print(f"Error fetching plan from Firestore: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve plan: {e}")

@router.post("/feedback", response_model=FeedbackInDB)
async def submit_feedback(feedback_data: FeedbackCreate, current_user: dict = Depends(get_current_user)):
    """Receives feedback on a specific learning plan and saves to Firestore."""
    if not db:
        raise HTTPException(status_code=500, detail="Firestore client not initialized")
        
    user_id = current_user["id"]
    timestamp = datetime.datetime.utcnow()
    
    # Check if the plan exists (optional but good practice)
    plan_ref = plans_collection.document(feedback_data.plan_id)
    if not plan_ref.get().exists:
        raise HTTPException(status_code=404, detail=f"Plan with ID {feedback_data.plan_id} not found")
        
    feedback_doc_data = feedback_data.dict()
    feedback_doc_data["user_id"] = user_id
    feedback_doc_data["created_at"] = timestamp
    
    try:
        # Add the feedback document
        update_time, doc_ref = feedback_collection.add(feedback_doc_data)
        print(f"Feedback saved for user {user_id} on plan {feedback_data.plan_id} with doc ID: {doc_ref.id}")
        
        # Prepare response model
        response_data = feedback_doc_data.copy()
        response_data["id"] = doc_ref.id
        return FeedbackInDB(**response_data)
        
    except Exception as e:
        print(f"Error saving feedback to Firestore: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {e}")


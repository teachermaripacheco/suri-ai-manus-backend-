from pydantic import BaseModel, Field
from typing import List, Optional

class StudentInputBase(BaseModel):
    goals: List[str]
    struggles: str

class StudentInputCreate(StudentInputBase):
    pass

class StudentInputInDB(StudentInputBase):
    user_id: str
    id: str # Document ID in Firebase

    class Config:
        from_attributes = True

class PlanActivity(BaseModel):
    type: str
    title: str
    duration: str

class PlanBase(BaseModel):
    week: int
    theme: str
    goals: List[str]
    activities: List[PlanActivity]
    focusAreas: List[str]

class PlanCreate(PlanBase):
    user_id: str # Link to the user

class PlanInDB(PlanBase):
    user_id: str
    id: str # Document ID in Firebase

    class Config:
        from_attributes = True

class FeedbackBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = None
    plan_id: str # Link to the specific plan being reviewed

class FeedbackCreate(FeedbackBase):
    user_id: str # Link to the user giving feedback

class FeedbackInDB(FeedbackBase):
    user_id: str
    id: str # Document ID in Firebase

    class Config:
        from_attributes = True


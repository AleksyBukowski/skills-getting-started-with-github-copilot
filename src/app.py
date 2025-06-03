"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from pymongo import MongoClient
from typing import Dict, List

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['mergington_high']
activities_collection = db['activities']

# Initial activities data
initial_activities = {
    "Soccer Team": {
        "description": "Join the school soccer team and compete in local leagues",
        "schedule": "Wednesdays and Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 18,
        "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
    },
    "Basketball Club": {
        "description": "Practice basketball skills and play friendly matches",
        "schedule": "Tuesdays, 5:00 PM - 6:30 PM",
        "max_participants": 15,
        "participants": ["liam@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore painting, drawing, and other visual arts",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 20,
        "participants": ["ava@mergington.edu"]
    },
    "Drama Society": {
        "description": "Participate in school plays and acting workshops",
        "schedule": "Mondays, 4:00 PM - 5:30 PM",
        "max_participants": 25,
        "participants": ["noah@mergington.edu"]
    },
    "Math Olympiad": {
        "description": "Prepare for math competitions and solve challenging problems",
        "schedule": "Fridays, 2:00 PM - 3:30 PM",
        "max_participants": 10,
        "participants": ["emma@mergington.edu", "oliver@mergington.edu"]
    }
}

# Initialize database with activities if empty
@app.on_event("startup")
async def init_db():
    if activities_collection.count_documents({}) == 0:
        for name, details in initial_activities.items():
            activities_collection.insert_one({"name": name, **details})

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
async def get_activities():
    activities = {}
    cursor = activities_collection.find({}, {'_id': 0})
    for activity in cursor:
        name = activity.pop('name')
        activities[name] = activity
    return activities



@app.post("/activities/{activity_name}/signup")
async def signup_for_activity(activity_name: str, email: str):
    # Get the activity
    activity = activities_collection.find_one({"name": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Check if already registered
    participants = activity.get("participants", [])
    if email in participants:
        raise HTTPException(status_code=400, detail="Already registered for this activity")
    
    # Check if activity is full
    if len(participants) >= activity.get("max_participants", 0):
        raise HTTPException(status_code=400, detail="Activity is full")
    
    # Add participant
    result = activities_collection.update_one(
        {"name": activity_name},
        {"$addToSet": {"participants": email}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to register for activity")
    
    return {"message": f"Successfully registered for {activity_name}"}


# Unregister endpoint
@app.post("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Remove a student from an activity"""
    # Get the activity
    activity = activities_collection.find_one({"name": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Check if registered
    if email not in activity.get("participants", []):
        raise HTTPException(status_code=404, detail="Participant not found in this activity")
    
    # Remove participant
    result = activities_collection.update_one(
        {"name": activity_name},
        {"$pull": {"participants": email}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to unregister from activity")
    
    return {"message": f"Removed {email} from {activity_name}"}

from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from executor import run_code
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

import os
import uuid
import datetime

load_dotenv()

uri = os.getenv("DB_URI")

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["submission"]


app = FastAPI()

limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def show_ui():
    return FileResponse("frontend.html")

class Data(BaseModel):
    code : str
    
@app.post("/submit", status_code=201)
@limiter.limit("1/3seconds")
async def submit_code(data : Data, request: Request):
    
    now = datetime.datetime.now()   
    print(now) 
    
    if len(data.code) > 10000:
        return {"output": "// ERROR: Code exceeds maximum length", "status": "ERROR", "execution_time": None}
        
    job_id = str(uuid.uuid4())

    

    print(request.client.host)
    report = run_code(data.code)
    submission_data = {"job_id": job_id, "code" : data.code, "output": report.get("output"), "status": report.get("status"), 
            "execution_time": report.get("execution_time"),  "submitted_at": now,
            "ip" : request.client.host}
    
    db["submissions"].insert_one(submission_data)
    submission_data.pop("_id", None)
    return submission_data

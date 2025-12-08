from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="RAG Gemini Backend")

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "RAG Backend Running!"}

# Temporary test endpoint for PDF upload
# (we will implement real processing in Part 4)
@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    return {"filename": file.filename, "status": "received"}

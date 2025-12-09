from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai
import os

import shutil
from app.pdf_utils import extract_text_from_pdf, chunk_text

load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel("gemini-2.5-flash")

app = FastAPI(title="RAG Gemini Backend")

# Allow frontend
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

# upload_pdf
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Save PDF, extract text, split into chunks.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    # Save uploaded PDF
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Extract text
    full_text = extract_text_from_pdf(file_path)
    chunks = chunk_text(full_text, chunk_size=500, overlap=50)

    return {
        "filename": file.filename,
        "status": "processed",
        "num_chunks": len(chunks),
        "sample_chunk": chunks[0] if chunks else ""
    }


@app.post("/query")
def query_gemini(payload: dict):
    prompt = payload.get("prompt", "")

    try:
        response = model.generate_content(prompt)
        return {"response": response.text}
    except Exception as e:
        return {"error": str(e)}

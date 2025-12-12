from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os

from dotenv import load_dotenv
load_dotenv()

import shutil
import uuid
from app.pdf_utils import extract_text_from_pdf, chunk_text
from app.embeddings import get_embedding
from app.pinecone_client import index




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
    Upload PDF → extract → chunk → embed → upsert to Pinecone
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save PDF
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Extract + chunk
    text = extract_text_from_pdf(file_path)
    chunks = chunk_text(text, chunk_size=500, overlap=50)

    # Build Pinecone vectors
    vectors = []
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)  # 1024 dims
        vectors.append({
            "id": f"{file.filename}-{i}",
            "values": embedding,
            "metadata": {
                "text": chunk,       
                "chunk_id": i,
                "source": file.filename
            }
        })

    # Upsert into Pinecone
    index.upsert(vectors)

    return {
        "filename": file.filename,
        "num_chunks": len(chunks),
        "status": "Successfully embedded and stored in Pinecone!"
    }


from app.embeddings import get_embedding
from app.pinecone_client import index

@app.post("/rag_query")
def rag_query(payload: dict):
    query_text = payload.get("query", "")

    # 1. Create embedding for query
    query_embedding = get_embedding(query_text)

    # 2. Search Pinecone
    search_results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True
    )

    # 3. Build context string
    context = "\n".join([m["metadata"]["text"] for m in search_results.matches])

    # 4. Ask Gemini
    final_prompt = f"Use ONLY the context below to answer.\n\nContext:\n{context}\n\nQuestion: {query_text}"

    response = model.generate_content(final_prompt)

    return {
        "context_used": context,
        "answer": response.text
    }

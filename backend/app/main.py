from fastapi import FastAPI, UploadFile, File, Body, Form
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
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """
    Upload PDF → extract → chunk → embed → upsert to Pinecone
    Linked to ONE session_id
    """

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    text = extract_text_from_pdf(file_path)
    chunks = chunk_text(text, chunk_size=500, overlap=50)

    vectors = []
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)

        vectors.append({
            "id": f"{session_id}-{i}",   
            "values": embedding,
            "metadata": {
                "text": chunk,
                "chunk_id": i,
                "source": file.filename,
                "session_id": session_id 
            }
        })

    index.upsert(vectors)

    return {
        "session_id": session_id,
        "filename": file.filename,
        "chunks_stored": len(chunks)
    }


from app.embeddings import get_embedding
from app.pinecone_client import index

@app.post("/query")
def query_pdf(payload: dict = Body(...)):
    """
    Query PDF content using session_id filtering
    Supports follow-up questions with intelligent rewriting
    """

    session_id = payload.get("session_id")
    question = payload.get("question")
    is_followup = payload.get("is_followup", False)
    previous_answer = payload.get("previous_answer", "")

    if not session_id or not question:
        return {"error": "session_id and question are required"}

    # --------------------------------------------------
    # Step 1: Decide retrieval query
    # --------------------------------------------------

    if is_followup and previous_answer:
        rewrite_prompt = f"""
        You are a query-rewriting assistant.
        Your task is to rewrite a follow-up question into a clear and search-optimized standalone question.

        You will be provided with the previous answer and the follow-up question.

        Instructions:
        1. Infer the missing keyword in the follow-up question using the previous answer (not the whole context of the answer).
        2. Resolve vague references (e.g., "above", "this", "2nd point", "that").
        3. Rewrite the question so it can be understood without seeing the previous answer.
        4. Preserve the original intent and scope of the follow-up question.
        5. Do NOT answer the question.
        6. Output ONLY the rewritten standalone question.


        Inputs:
        - Previous answer: {previous_answer}
        - Follow-up question: {question}
        """

        retrieval_query = model.generate_content(
            rewrite_prompt
        ).text.strip()

    else:
        # First question → no rewrite
        retrieval_query = question

    # --------------------------------------------------
    # Step 2: Embed retrieval query
    # --------------------------------------------------

    query_embedding = get_embedding(retrieval_query)

    # --------------------------------------------------
    # Step 3: Pinecone query (session-scoped)
    # --------------------------------------------------

    results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True,
        filter={
            "session_id": {"$eq": session_id}
        }
    )

    if not results.matches:
        return {
            "answer": "I don't know",
            "retrieval_query": retrieval_query
        }

    # --------------------------------------------------
    # Step 4: Build context
    # --------------------------------------------------

    context = "\n\n".join(
        match.metadata["text"] for match in results.matches
    )

    # --------------------------------------------------
    # Step 5: Answer using Gemini
    # --------------------------------------------------

    answer_prompt = f"""
    You are an assistant answering questions ONLY using the context below.
    If the answer is not present, say "I don't know".

    Context:
    {context}

    Question:
    {question}
    """

    answer = model.generate_content(answer_prompt).text.strip()

    return {
        "session_id": session_id,
        "question": question,
        "is_followup": is_followup,
        "retrieval_query": retrieval_query,
        "answer": answer
    }
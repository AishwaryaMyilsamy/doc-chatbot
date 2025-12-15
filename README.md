# 📄 DOCU-MIND

**Session-based PDF Question Answering System**

DOCU-MIND is a full-stack application that allows users to upload a PDF and ask questions **only within the context of that PDF**, using a **single session**. Follow-up questions are intelligently handled without storing chat history.

---

## 🚀 Features

* 📂 Upload PDF files
* ✂️ Automatic text extraction and chunking
* 🧠 Embedding + semantic search using Pinecone
* 🔐 Session-based isolation (no cross-PDF leakage)
* 🔁 Intelligent follow-up question handling
* ⚡ FastAPI backend + Streamlit frontend
* ❌ No chat history stored (single-session scope)

---

## 🧠 Architecture Overview

```
Frontend (Streamlit)
   |
   |  Upload PDF / Ask Question
   v
Backend (FastAPI)
   |
   |  Extract → Chunk → Embed
   v
Pinecone Vector DB (session_id filtered)
   |
   |  Retrieved context
   v
Gemini (Answer Generation)
```

---

## 🧩 Key Concepts

### 1. Session-Based Isolation

* A **session_id** is generated when the frontend loads.
* All PDF chunks are stored in Pinecone with this `session_id`.
* Queries only retrieve chunks matching the same `session_id`.
* Refreshing the page → new session → clean slate.

---

### 2. No Chat History

* Previous answers are **not stored in the database**.
* Only the **last answer** is used temporarily for follow-up question rewriting.
* Keeps the system stateless and lightweight.

---

### 3. Follow-Up Question Handling

* First question → used as-is
* Follow-up question → rewritten using:

  * Current question
  * Previous answer


---

## 📁 Project Structure

```
doc-chatbot/
│
├── backend/
│   └── app/
│       ├── main.py               # FastAPI routes
│       ├── pinecone_client.py    # Pinecone setup
│       ├── embeddings.py         # Embedding logic
│       ├── pdf_utils.py          # PDF extraction
│       └── text_utils.py         # Chunking logic
│   
│
├── frontend/
│   └── streamlit_app.py          # Streamlit UI
│
├── requirements.txt
└── README.md
```

---

## 🔧 Backend Setup (FastAPI)

### 1. Environment Variables

Set the following in your shell or `.env` file:

```
PINECONE_API_KEY=your_key
PINECONE_INDEX_NAME=your_index
GEMINI_API_KEY=your_key
```

---

### 2. Run Backend Server

```
cd backend
uvicorn app.main:app --reload
```

Server runs at:

```
http://127.0.0.1:8000
```

---

## 📡 Backend Endpoints

### 1️⃣ Upload PDF

**POST** `/upload_pdf`

* Creates session-aware embeddings
* Stores chunks in Pinecone

**Request**

* multipart/form-data

  * `file`: PDF
  * `session_id`: UUID

**Response**

```
{
  "message": "PDF uploaded successfully and ready to answer questions"
}
```

---

### 2️⃣ Query PDF

**POST** `/query`

**Request JSON**

```
{
  "session_id": "uuid",
  "question": "Your question",
  "is_followup": true/false,
  "previous_answer": "optional"
}
```

**Response**

```
{
  "session_id": "...",
  "question": "...",
  "rewritten_question": "...",
  "answer": "..."
}
```

---

## 🖥️ Frontend Setup (Streamlit)

### Run Streamlit App

```
cd frontend
streamlit run streamlit_app.py
```

App runs at:

```
http://localhost:8501
```

---

## 🧠 Frontend Logic

* Auto-generates `session_id`
* Uploads PDF once per session
* Detects follow-up automatically:

  * If previous questions exist → follow-up = true
* Sends minimal payload to backend

---

## 🔁 Streamlit Session Flow

1. Page loads → session_id created
2. User uploads PDF → chunks stored with session_id
3. User asks question → retrieves chunks for session_id
4. Follow-up questions are rewritten automatically
5. Refresh page → new session → new PDF

---

## 🛠️ Common Issues & Solutions

### ❌ PDF uploads again when asking question

✔ Fix: Track upload using `st.session_state` flag

---

### ❌ No answer but no error

✔ Cause:

* No Pinecone matches
* Gemini quota exceeded

✔ Fix:

* Log backend responses
* Add retry / wait for quota reset

---

### ❌ Gemini 429 Error

✔ Free tier has strict limits
✔ Wait ~60 seconds or reduce calls
✔ Embedding + generation both count

---

## 🚀 Deployment (High-Level)

### Backend

* Render / Railway / EC2 / Fly.io
* Add env vars in dashboard
* Use production ASGI server

### Frontend

* Streamlit Community Cloud
* Point API URLs to deployed backend

---

## 🔐 Security Notes

* Never commit API keys
* Use `.env` files
* Restrict Pinecone index access

---

## 🧪 Tested With

* Postman (API validation)
* Streamlit UI
* Pinecone dashboard
* Gemini API free tier

---

## 🏁 Final Notes

* Designed for **single-session PDF Q&A**
* Lightweight and scalable
* Easy to extend to multi-session or chat history later



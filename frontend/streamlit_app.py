import streamlit as st
import requests
import uuid

# -----------------------------
# Session ID Management
# -----------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "questions" not in st.session_state:
    st.session_state.questions = []
if "answers" not in st.session_state:
    st.session_state.answers = []

session_id = st.session_state.session_id

st.title("DOCU-MIND")

# -----------------------------
# PDF Upload Section
# -----------------------------
st.header("Upload PDF")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None and "uploaded" not in st.session_state:
    with st.spinner("Uploading and processing PDF..."):
        files = {"file": uploaded_file}
        data = {"session_id": session_id}
        try:
            response = requests.post(
                "http://127.0.0.1:8000/upload_pdf",
                files=files,
                data=data
            )
            response.raise_for_status()
            res_json = response.json()
            st.success(res_json.get("message", " PDF uploaded successfully!"))
        except Exception as e:
            st.error(f"Upload failed: {e}")

# -----------------------------
# Ask Question Section
# -----------------------------
st.header("Ask a Question")
question = st.text_input("Enter your question:")

if st.button("Ask"):
    if not question:
        st.warning("Please enter a question.")
    else:
        # Determine if follow-up automatically
        is_followup = len(st.session_state.questions) > 0
        previous_answer = st.session_state.answers[-1] if is_followup else ""

        payload = {
            "session_id": session_id,
            "question": question,
            "is_followup": is_followup,
            "previous_answer": previous_answer
        }
        try:
            response = requests.post("http://127.0.0.1:8000/query", json=payload)
            response.raise_for_status()
            res_json = response.json()
            # st.write(res_json) (to degug)
            
            st.subheader("Answer:")
            st.write(res_json.get("answer", "No answer found."))

            if is_followup:
                st.subheader("Rewritten Question (Follow-up):")
                st.write(res_json.get("rewritten_question", ""))

            # Save question and answer for next follow-up
            st.session_state.questions.append(question)
            st.session_state.answers.append(res_json.get("answer", ""))
                
        except Exception as e:
            st.error(f"Query failed: {e}")

# -----------------------------
# Display Session ID
# -----------------------------
st.sidebar.header("Session Info")
st.sidebar.write(f"Session ID: {session_id}")
st.sidebar.info("Refreshing the page will generate a new session ID.")

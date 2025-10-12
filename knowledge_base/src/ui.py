import os
import streamlit as st
from typing import List
from dotenv import load_dotenv

from .config import OPENAI_API_KEY, CHUNK_SIZE, CHUNK_OVERLAP
from .pdf_ingest import chunk_pdf
from .vector_store import get_vector_store, add_documents, search
from langchain.chat_models import ChatOpenAI

load_dotenv()

st.set_page_config(page_title="Knowledge Engine (PDF)", page_icon="📚", layout="wide")

st.title("📚 Knowledge Engine — PDF MVP")

# Topic selection
with st.sidebar:
	st.header("Topic")
	topic = st.text_input("Topic/Collection name", value="default")
	st.caption("Each topic creates its own vector collection.")

	st.header("Chunking")
	st.write(f"Chunk size: {CHUNK_SIZE}, overlap: {CHUNK_OVERLAP}")

	st.header("Status")
	if OPENAI_API_KEY:
		st.success("OpenAI key detected")
	else:
		st.error("Missing OPENAI_API_KEY")

# Initialize vector store per topic
if "vs_topic" not in st.session_state or st.session_state.vs_topic != topic:
	st.session_state.vs = get_vector_store(topic)
	st.session_state.vs_topic = topic
	st.session_state.chat = []

# Upload & ingest PDFs
st.subheader("Upload PDFs")
files = st.file_uploader("Upload one or more PDFs", type=["pdf"], accept_multiple_files=True)

if files and st.button("Ingest PDFs"):
	progress = st.progress(0)
	total = len(files)
	added = 0
	for i, f in enumerate(files, start=1):
		with st.spinner(f"Processing {f.name}..."):
			# Save temp
			path = os.path.join("data/raw", f.name)
			os.makedirs("data/raw", exist_ok=True)
			with open(path, "wb") as out:
				out.write(f.getbuffer())
			# Chunk
			docs = chunk_pdf(path, topic)
			# Add to vector store
			ids = add_documents(st.session_state.vs, docs)
			added += len(ids)
		progress.progress(i/total)
	st.success(f"Ingested {total} files, {added} chunks added")

st.divider()

# Chat
st.subheader("Chat with your PDFs")
for m in st.session_state.chat:
	with st.chat_message(m["role"]):
		st.markdown(m["content"])

query = st.chat_input("Ask a question about this topic")
if query:
	st.session_state.chat.append({"role": "user", "content": query})
	with st.chat_message("user"):
		st.markdown(query)
	with st.chat_message("assistant"):
		with st.spinner("Thinking..."):
			# retrieve
			docs = search(st.session_state.vs, query, k=5)
			context = "\n\n".join(d.page_content for d in docs)
			# generate
			llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
			prompt = f"""
You are a helpful research assistant. Answer the question using only the provided context.
Cite sources by file name and page when possible.
If insufficient info, say what is missing.

Context:
{context}

Question: {query}
"""
			resp = llm.invoke(prompt).content
			st.markdown(resp)
			# sources
			with st.expander("Sources"):
				for i, d in enumerate(docs, 1):
					fname = d.metadata.get("file_name", "unknown")
					st.write(f"{i}. {fname}")
			st.session_state.chat.append({"role": "assistant", "content": resp})

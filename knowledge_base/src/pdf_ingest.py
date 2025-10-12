import os
import hashlib
from typing import List, Dict
import pdfplumber
from langchain.schema import Document
from .config import CHUNK_SIZE, CHUNK_OVERLAP
from langchain.text_splitter import RecursiveCharacterTextSplitter


def _checksum(path: str) -> str:
	with open(path, 'rb') as f:
		return hashlib.md5(f.read()).hexdigest()


def extract_text_with_pages(path: str) -> List[Dict]:
	pages = []
	with pdfplumber.open(path) as pdf:
		for i, p in enumerate(pdf.pages, start=1):
			text = p.extract_text() or ""
			pages.append({"page": i, "text": text})
	return pages


def chunk_pdf(path: str, topic: str) -> List[Document]:
	pages = extract_text_with_pages(path)
	full_text = "\n\n".join([f"--- Page {p['page']} ---\n{p['text']}" for p in pages if p['text'].strip()])
	splitter = RecursiveCharacterTextSplitter(
		separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
		chunk_size=CHUNK_SIZE,
		chunk_overlap=CHUNK_OVERLAP,
		length_function=len,
	)
	docs = splitter.create_documents([full_text])
	file_name = os.path.basename(path)
	fingerprint = _checksum(path)
	for idx, d in enumerate(docs):
		d.metadata.update({
			"source_type": "pdf",
			"file_name": file_name,
			"checksum": fingerprint,
			"topic": topic,
			"chunk_index": idx,
		})
	return docs

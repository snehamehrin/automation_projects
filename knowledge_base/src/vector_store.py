from typing import List, Optional, Dict, Any
import os
import chromadb
from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from .config import CHROMA_DIR, COLLECTION_NAME, OPENAI_API_KEY, EMBEDDING_MODEL


def get_vector_store(topic: str) -> Chroma:
	os.makedirs(CHROMA_DIR, exist_ok=True)
	client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
	try:
		client.get_collection(f"{COLLECTION_NAME}_{topic}")
	except:
		client.create_collection(f"{COLLECTION_NAME}_{topic}")
	embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model=EMBEDDING_MODEL)
	vs = Chroma(client=client, collection_name=f"{COLLECTION_NAME}_{topic}", embedding_function=embeddings)
	return vs


def add_documents(vs: Chroma, documents: List[Document]) -> List[str]:
	if not documents:
		return []
	return vs.add_documents(documents)


def search(vs: Chroma, query: str, k: int = 8, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
	if filters:
		return vs.similarity_search(query, k=k, filter=filters)
	return vs.similarity_search(query, k=k)

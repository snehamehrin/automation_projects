import os
import streamlit as st
import hashlib
import re
import unicodedata
import json
from typing import List, Dict, Tuple
import pdfplumber
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
import time
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import PorterStemmer
import spacy
from langchain_community.vectorstores.utils import filter_complex_metadata

# Install cross-encoder for reranking
try:
    from sentence_transformers import CrossEncoder
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    st.warning("Install sentence-transformers for better reranking: pip install sentence-transformers")

load_dotenv()

# Download required NLTK data
def download_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab')
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

# Download NLTK data on startup
download_nltk_data()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./database")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "300"))
COLLECTION_NAME = "knowledge_engine_pdf"

class AdvancedRAG:
    def __init__(self, vector_db, llm):
        self.vector_db = vector_db
        self.llm = llm
        if RERANKER_AVAILABLE:
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
        else:
            self.reranker = None
    
    def expand_query(self, user_question: str) -> List[str]:
        """Generate multiple related queries for comprehensive retrieval"""
        expansion_prompt = f"""Given this user question: "{user_question}"

Generate 5-7 specific sub-queries that would help answer this comprehensively.
Consider:
- Different aspects of the main topic
- Related concepts and synonyms
- Contrasting viewpoints
- Specific examples
- Quantitative vs qualitative angles
- Different perspectives on the same topic

Return as a JSON list of strings, like: ["query1", "query2", "query3"]"""

        try:
            response = self.llm.invoke(expansion_prompt).content
            # Extract JSON from response
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                queries = json.loads(json_match.group())
                return queries[:7]  # Limit to 7 queries
            else:
                # Fallback to simple query variations
                return [
                    user_question,
                    f"different perspectives on {user_question}",
                    f"examples of {user_question}",
                    f"factors affecting {user_question}",
                    f"comparison of {user_question}"
                ]
        except Exception as e:
            st.warning(f"Query expansion failed: {e}")
            return [user_question]
    
    def multi_query_retrieval(self, user_question: str, top_k: int = 20) -> List[Document]:
        """Retrieve using multiple query variations"""
        expanded_queries = self.expand_query(user_question)
        
        all_chunks = []
        for query in expanded_queries:
            try:
                chunks = self.vector_db.similarity_search(query, k=top_k//len(expanded_queries))
                all_chunks.extend(chunks)
            except Exception as e:
                st.warning(f"Retrieval failed for query '{query}': {e}")
        
        return all_chunks
    
    def deduplicate_chunks(self, chunks: List[Document]) -> List[Document]:
        """Remove duplicate chunks based on content"""
        seen_content = set()
        unique_chunks = []
        
        for chunk in chunks:
            content_hash = hashlib.md5(chunk.page_content.encode()).hexdigest()
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_chunks.append(chunk)
        
        return unique_chunks
    
    def rerank_chunks(self, query: str, chunks: List[Document], top_k: int = 15) -> List[Document]:
        """Rerank chunks using cross-encoder for better relevance"""
        if not self.reranker or len(chunks) <= top_k:
            return chunks[:top_k]
        
        try:
            # Prepare pairs for reranking
            pairs = [[query, chunk.page_content] for chunk in chunks]
            scores = self.reranker.predict(pairs)
            
            # Sort by relevance score
            reranked_chunks = [
                chunk for chunk, score in 
                sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
            ]
            
            return reranked_chunks[:top_k]
        except Exception as e:
            st.warning(f"Reranking failed: {e}")
            return chunks[:top_k]
    
    def group_by_source(self, chunks: List[Document]) -> Dict[str, List[Document]]:
        """Group chunks by source book for comparison"""
        sources = {}
        for chunk in chunks:
            source = chunk.metadata.get('file_name', 'unknown')
            if source not in sources:
                sources[source] = []
            sources[source].append(chunk)
        return sources
    
    def format_context_with_sources(self, sources: Dict[str, List[Document]]) -> str:
        """Format context with clear source attribution"""
        context_parts = []
        
        for source, chunks in sources.items():
            context_parts.append(f"## From {source}:")
            for i, chunk in enumerate(chunks, 1):
                context_parts.append(f"### Excerpt {i}:")
                context_parts.append(chunk.page_content)
                context_parts.append("")  # Add spacing
        
        return "\n".join(context_parts)
    
    def generate_synthesis(self, question: str, sources: Dict[str, List[Document]]) -> str:
        """Generate sophisticated synthesis with comparison and analysis"""
        context = self.format_context_with_sources(sources)
        
        synthesis_prompt = f"""You are an expert analyst synthesizing insights from multiple business books.

USER QUESTION: {question}

RETRIEVED CONTEXT FROM SOURCES:
{context}

INSTRUCTIONS:
1. **Synthesize, don't summarize**: Compare perspectives across sources
2. **Organize thematically**: Group by concepts, not by source
3. **Be specific**: Reference exact examples, frameworks, numbers from the text
4. **Show relationships**: How do concepts connect? Where do authors agree/disagree?
5. **Add analysis**: What patterns emerge? What are the implications?
6. **Structure clearly**: Use headers, bullets, tables
7. **Cite sources**: Mention which book/author when making claims

REQUIRED FORMAT:
1. Start with a 2-3 sentence executive summary
2. Organize into 3-7 major themes with ## headers
3. Use bullet points for key details
4. Include comparison tables where relevant
5. Provide specific examples from the text
6. End with synthesis/meta-insights

QUALITY STANDARDS:
- Would this answer satisfy a graduate student researching the topic?
- Does it go beyond just retrieval to provide genuine insight?
- Is it well-organized and easy to scan?
- Does it make connections the reader might not see?

Now provide a comprehensive, analytical response."""

        return self.llm.invoke(synthesis_prompt).content
    
    def answer_question(self, user_question: str) -> Tuple[str, Dict[str, List[Document]]]:
        """Complete advanced RAG pipeline"""
        # Step 1: Multi-query retrieval
        all_chunks = self.multi_query_retrieval(user_question, top_k=30)
        
        # Step 2: Deduplicate
        unique_chunks = self.deduplicate_chunks(all_chunks)
        
        # Step 3: Rerank for relevance
        top_chunks = self.rerank_chunks(user_question, unique_chunks, top_k=15)
        
        # Step 4: Group by source
        sources = self.group_by_source(top_chunks)
        
        # Step 5: Generate synthesis
        answer = self.generate_synthesis(user_question, sources)
        
        return answer, sources

class AdvancedTextProcessor:
    def __init__(self):
        self.stemmer = PorterStemmer()
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            st.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def clean_text(self, text: str) -> str:
        """Advanced text cleaning"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Remove page numbers and headers/footers
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[A-Z\s]{2,}$', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract named entities using spaCy"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        entities = []
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT']:
                entities.append(ent.text)
        return list(set(entities))
    
    def extract_keywords(self, text: str, max_keywords: int = 15) -> List[str]:
        """Extract keywords using TF-IDF-like approach"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        keywords = []
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 4:  # Keep longer phrases
                keywords.append(chunk.text.lower())
        
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 2):
                keywords.append(token.text.lower())
        
        return list(set(keywords))[:max_keywords]
    
    def semantic_chunk(self, text: str, chunk_size: int = 1000, overlap: int = 300) -> List[Dict]:
        """Advanced semantic chunking that preserves context"""
        # Split into paragraphs first
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        current_length = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            paragraph_length = len(paragraph)
            
            # If adding this paragraph would exceed chunk size, save current chunk
            if current_length + paragraph_length > chunk_size and current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'length': current_length,
                    'type': 'semantic_chunk'
                })
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + "\n\n" + paragraph
                current_length = len(current_chunk)
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
                current_length += paragraph_length
        
        # Add the last chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'length': current_length,
                'type': 'semantic_chunk'
            })
        
        return chunks
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get the last part of text for overlap"""
        words = text.split()
        if len(words) <= overlap_size:
            return text
        return " ".join(words[-overlap_size:])

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

def process_pdf_advanced(path: str, topic: str) -> List[Document]:
    """Advanced PDF processing with semantic chunking"""
    processor = AdvancedTextProcessor()
    pages = extract_text_with_pages(path)
    
    # Combine all pages
    full_text = "\n\n".join([f"--- Page {p['page']} ---\n{p['text']}" for p in pages if p['text'].strip()])
    
    # Clean the text
    cleaned_text = processor.clean_text(full_text)
    
    # Extract metadata
    entities = processor.extract_entities(cleaned_text)
    keywords = processor.extract_keywords(cleaned_text)
    
    # Semantic chunking
    chunks_data = processor.semantic_chunk(cleaned_text, CHUNK_SIZE, CHUNK_OVERLAP)
    
    # Create documents with rich metadata
    docs = []
    file_name = os.path.basename(path)
    fingerprint = _checksum(path)
    
    for idx, chunk_data in enumerate(chunks_data):
        doc = Document(
            page_content=chunk_data['text'],
            metadata={
                "source_type": "pdf",
                "file_name": file_name,
                "checksum": fingerprint,
                "topic": topic,
                "chunk_index": idx,
                "chunk_length": chunk_data['length'],
                "entities": ", ".join(entities[:8]),
                "keywords": ", ".join(keywords[:8]),
                "page_range": f"pages {pages[0]['page']}-{pages[-1]['page']}" if pages else "unknown",
                "chunk_type": chunk_data['type']
            }
        )
        docs.append(doc)
    
    return docs

def get_chroma_client():
    """Get ChromaDB client"""
    os.makedirs(CHROMA_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))

def get_available_collections():
    """Get list of available collections"""
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        return [col.name for col in collections if col.name.startswith(COLLECTION_NAME)]
    except Exception as e:
        st.error(f"Error getting collections: {str(e)}")
        return []

def get_collection_info(collection_name: str):
    """Get information about a collection"""
    try:
        client = get_chroma_client()
        collection = client.get_collection(collection_name)
        count = collection.count()
        return {
            "name": collection_name,
            "count": count,
            "topic": collection_name.replace(f"{COLLECTION_NAME}_", "")
        }
    except Exception as e:
        return None

def delete_collection(collection_name: str):
    """Delete a collection"""
    try:
        client = get_chroma_client()
        client.delete_collection(collection_name)
        return True
    except Exception as e:
        st.error(f"Error deleting collection: {str(e)}")
        return False

def get_vector_store(topic: str) -> Chroma:
    client = get_chroma_client()
    try:
        client.get_collection(f"{COLLECTION_NAME}_{topic}")
    except:
        client.create_collection(f"{COLLECTION_NAME}_{topic}")
    
    # Use the larger embedding model
    embeddings = OpenAIEmbeddings(
        openai_api_key=OPENAI_API_KEY, 
        model=EMBEDDING_MODEL,
        chunk_size=100,
        max_retries=3
    )
    vs = Chroma(client=client, collection_name=f"{COLLECTION_NAME}_{topic}", embedding_function=embeddings)
    return vs

def add_documents_with_retry(vs: Chroma, documents: List[Document], max_retries: int = 3) -> List[str]:
    if not documents:
        return []
    
    # Filter complex metadata before adding to Chroma
    filtered_docs = filter_complex_metadata(documents)
    
    for attempt in range(max_retries):
        try:
            return vs.add_documents(filtered_docs)
        except Exception as e:
            st.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise e

# Streamlit UI
st.set_page_config(page_title="Advanced Knowledge Engine", page_icon="��", layout="wide")

st.title("🧠 Advanced Knowledge Engine — Expert-Level RAG")

# Initialize session state
if "selected_collection" not in st.session_state:
    st.session_state.selected_collection = None
if "vs" not in st.session_state:
    st.session_state.vs = None
if "chat" not in st.session_state:
    st.session_state.chat = []
if "rag" not in st.session_state:
    st.session_state.rag = None

# Sidebar for database management
with st.sidebar:
    st.header("🗄️ Vector Database Management")
    
    # Get available collections
    collections = get_available_collections()
    
    if collections:
        st.subheader("Available Collections")
        
        # Display collection info
        for collection_name in collections:
            info = get_collection_info(collection_name)
            if info:
                with st.expander(f"📁 {info['topic']} ({info['count']} chunks)"):
                    st.write(f"**Collection:** {info['name']}")
                    st.write(f"**Documents:** {info['count']} chunks")
                    st.write(f"**Topic:** {info['topic']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Select", key=f"select_{info['topic']}"):
                            st.session_state.selected_collection = info['topic']
                            st.session_state.vs = get_vector_store(info['topic'])
                            st.session_state.chat = []
                            # Initialize RAG
                            llm = ChatOpenAI(model="gpt-4o", temperature=0.1, openai_api_key=OPENAI_API_KEY)
                            st.session_state.rag = AdvancedRAG(st.session_state.vs, llm)
                            st.success(f"Selected: {info['topic']}")
                            st.rerun()
                    
                    with col2:
                        if st.button(f"🗑️", key=f"delete_{info['topic']}", help="Delete collection"):
                            if st.session_state.selected_collection == info['topic']:
                                st.session_state.selected_collection = None
                                st.session_state.vs = None
                                st.session_state.chat = []
                                st.session_state.rag = None
                            if delete_collection(collection_name):
                                st.success(f"Deleted: {info['topic']}")
                                st.rerun()
        
        # Current selection
        if st.session_state.selected_collection:
            st.success(f"✅ Active: {st.session_state.selected_collection}")
            
            if st.button("🔄 Refresh Collection"):
                st.session_state.vs = get_vector_store(st.session_state.selected_collection)
                llm = ChatOpenAI(model="gpt-4o", temperature=0.1, openai_api_key=OPENAI_API_KEY)
                st.session_state.rag = AdvancedRAG(st.session_state.vs, llm)
                st.success("Collection refreshed!")
                st.rerun()
    else:
        st.info("No collections found. Upload PDFs to create your first collection.")
    
    st.divider()
    
    # New collection creation
    st.subheader("Create New Collection")
    new_topic = st.text_input("New topic/collection name", placeholder="e.g., business_strategy")
    
    if st.button("Create Collection") and new_topic:
        try:
            st.session_state.vs = get_vector_store(new_topic)
            st.session_state.selected_collection = new_topic
            st.session_state.chat = []
            llm = ChatOpenAI(model="gpt-4o", temperature=0.1, openai_api_key=OPENAI_API_KEY)
            st.session_state.rag = AdvancedRAG(st.session_state.vs, llm)
            st.success(f"Created: {new_topic}")
            st.rerun()
        except Exception as e:
            st.error(f"Error creating collection: {str(e)}")

    st.divider()
    
    # Processing settings
    st.header("Advanced Processing")
    st.write(f"Chunk size: {CHUNK_SIZE}, overlap: {CHUNK_OVERLAP}")
    st.write("✅ Semantic chunking")
    st.write("✅ Multi-query retrieval")
    st.write("✅ Cross-encoder reranking")
    st.write("✅ Source comparison")
    st.write("🧠 **Expert-level synthesis**")

    st.header("Status")
    if OPENAI_API_KEY:
        st.success("OpenAI key detected")
    else:
        st.error("Missing OPENAI_API_KEY")

# Main content area
if st.session_state.selected_collection and st.session_state.rag:
    st.subheader(f"📚 Active Collection: {st.session_state.selected_collection}")
    
    # Upload & ingest PDFs
    st.subheader("Upload PDFs")
    files = st.file_uploader("Upload one or more PDFs", type=["pdf"], accept_multiple_files=True)

    if files and st.button("Ingest PDFs"):
        progress = st.progress(0)
        status_text = st.empty()
        total = len(files)
        added = 0
        
        for i, f in enumerate(files, start=1):
            status_text.text(f"Processing {f.name} with advanced NLP...")
            try:
                # Save temp
                path = os.path.join("data/raw", f.name)
                os.makedirs("data/raw", exist_ok=True)
                with open(path, "wb") as out:
                    out.write(f.getbuffer())
                
                # Advanced processing
                docs = process_pdf_advanced(path, st.session_state.selected_collection)
                
                # Add to vector store with retry
                ids = add_documents_with_retry(st.session_state.vs, docs)
                added += len(ids)
                
                # Show processing details
                with st.expander(f"📊 Processing details for {f.name}"):
                    st.write(f"**Chunks created:** {len(docs)}")
                    if docs:
                        sample_doc = docs[0]
                        st.write(f"**Sample entities:** {sample_doc.metadata.get('entities', '')}")
                        st.write(f"**Sample keywords:** {sample_doc.metadata.get('keywords', '')}")
                        st.write(f"**Chunk length:** {sample_doc.metadata.get('chunk_length', 0)} chars")
                
                st.success(f"✅ {f.name}: {len(ids)} chunks added")
                
            except Exception as e:
                st.error(f"❌ Error processing {f.name}: {str(e)}")
            
            progress.progress(i/total)
        
        status_text.text("Processing complete!")
        st.success(f"🎉 Successfully processed {total} files with {added} total chunks!")
        st.rerun()

    st.divider()

    # Chat
    st.subheader("🧠 Advanced RAG Analysis")
    st.caption("Ask complex questions and get sophisticated, multi-source analysis with expert-level synthesis")

    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    query = st.chat_input("Ask a sophisticated question about this topic")
    if query:
        st.session_state.chat.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
        with st.chat_message("assistant"):
            with st.spinner("🧠 Conducting advanced RAG analysis..."):
                try:
                    # Use advanced RAG pipeline
                    answer, sources = st.session_state.rag.answer_question(query)
                    st.markdown(answer)
                    
                    # Enhanced sources with analysis
                    with st.expander("📚 Sources & Analysis"):
                        st.write("**Retrieved Sources:**")
                        for source, chunks in sources.items():
                            st.write(f"**📖 {source}** ({len(chunks)} chunks)")
                            for i, chunk in enumerate(chunks, 1):
                                entities = chunk.metadata.get("entities", "")
                                keywords = chunk.metadata.get("keywords", "")
                                st.write(f"  {i}. Chunk {chunk.metadata.get('chunk_index', '?')}")
                                if entities:
                                    st.write(f"     Entities: {entities}")
                                if keywords:
                                    st.write(f"     Keywords: {keywords}")
                                st.write(f"     Preview: {chunk.page_content[:200]}...")
                                st.write("     ---")
                    
                    st.session_state.chat.append({"role": "assistant", "content": answer})
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat.append({"role": "assistant", "content": error_msg})

else:
    st.info("👈 Please select a collection from the sidebar to start chatting with your documents.")
    
    # Show available collections if any
    collections = get_available_collections()
    if collections:
        st.subheader("Available Collections")
        for collection_name in collections:
            info = get_collection_info(collection_name)
            if info:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{info['topic']}**")
                with col2:
                    st.write(f"{info['count']} chunks")
                with col3:
                    if st.button(f"Select", key=f"main_select_{info['topic']}"):
                        st.session_state.selected_collection = info['topic']
                        st.session_state.vs = get_vector_store(info['topic'])
                        st.session_state.chat = []
                        llm = ChatOpenAI(model="gpt-4o", temperature=0.1, openai_api_key=OPENAI_API_KEY)
                        st.session_state.rag = AdvancedRAG(st.session_state.vs, llm)
                        st.rerun()

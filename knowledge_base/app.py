import os
import streamlit as st
import hashlib
import re
import unicodedata
from typing import List, Dict
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
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./database")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
COLLECTION_NAME = "knowledge_engine_pdf"

class TextProcessor:
    def __init__(self):
        self.stemmer = PorterStemmer()
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            st.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
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
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords using TF-IDF-like approach"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        # Get noun phrases and important words
        keywords = []
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 3:  # Keep short phrases
                keywords.append(chunk.text.lower())
        
        # Get important tokens
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 2):
                keywords.append(token.text.lower())
        
        # Remove duplicates and return top keywords
        return list(set(keywords))[:max_keywords]
    
    def smart_chunk(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """Smart chunking that respects sentence boundaries and topics"""
        # Split into sentences first
        sentences = sent_tokenize(text)
        
        chunks = []
        current_chunk = ""
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence would exceed chunk size, save current chunk
            if current_length + sentence_length > chunk_size and current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'length': current_length
                })
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + " " + sentence
                current_length = len(current_chunk)
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_length += sentence_length
        
        # Add the last chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'length': current_length
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
    """Advanced PDF processing with NLP"""
    processor = TextProcessor()
    pages = extract_text_with_pages(path)
    
    # Combine all pages
    full_text = "\n\n".join([f"--- Page {p['page']} ---\n{p['text']}" for p in pages if p['text'].strip()])
    
    # Clean the text
    cleaned_text = processor.clean_text(full_text)
    
    # Extract metadata
    entities = processor.extract_entities(cleaned_text)
    keywords = processor.extract_keywords(cleaned_text)
    
    # Smart chunking
    chunks_data = processor.smart_chunk(cleaned_text, CHUNK_SIZE, CHUNK_OVERLAP)
    
    # Create documents
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
                "entities": ", ".join(entities[:5]),  # Convert list to string
                "keywords": ", ".join(keywords[:5]),  # Convert list to string
                "page_range": f"pages {pages[0]['page']}-{pages[-1]['page']}" if pages else "unknown"
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
    
    # Use the newer OpenAIEmbeddings from langchain_openai
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

def intelligent_search(vs: Chroma, query: str, k: int = 12) -> List[Document]:
    """Enhanced search with multiple strategies"""
    # Strategy 1: Direct similarity search
    direct_results = vs.similarity_search(query, k=k//2)
    
    # Strategy 2: Search for key concepts
    query_words = query.lower().split()
    concept_results = []
    for word in query_words:
        if len(word) > 3:  # Skip short words
            concept_results.extend(vs.similarity_search(word, k=2))
    
    # Strategy 3: Search for related terms
    related_terms = []
    if "commitment" in query.lower():
        related_terms.extend(["motivation", "willingness", "reluctance", "attachment", "dedication"])
    if "seller" in query.lower():
        related_terms.extend(["owner", "entrepreneur", "founder", "proprietor"])
    if "approach" in query.lower():
        related_terms.extend(["method", "strategy", "philosophy", "perspective", "framework"])
    if "theme" in query.lower() or "themes" in query.lower():
        related_terms.extend(["pattern", "recurring", "consistent", "underlying", "fundamental"])
    if "factor" in query.lower() or "factors" in query.lower():
        related_terms.extend(["influence", "determinant", "driver", "element", "component"])
    
    related_results = []
    for term in related_terms:
        related_results.extend(vs.similarity_search(term, k=2))
    
    # Combine and deduplicate
    all_results = direct_results + concept_results + related_results
    seen_content = set()
    unique_results = []
    
    for doc in all_results:
        if doc.page_content not in seen_content:
            seen_content.add(doc.page_content)
            unique_results.append(doc)
    
    return unique_results[:k]

def create_sophisticated_prompt(query: str, docs: List[Document]) -> str:
    """Create a sophisticated prompt that generates deep, analytical responses"""
    
    # Extract source information
    sources = {}
    for doc in docs:
        file_name = doc.metadata.get("file_name", "unknown")
        if file_name not in sources:
            sources[file_name] = []
        sources[file_name].append(doc.page_content)
    
    # Build context with source attribution
    context_parts = []
    for file_name, contents in sources.items():
        context_parts.append(f"## From {file_name}:")
        for content in contents:
            context_parts.append(content)
        context_parts.append("")  # Add spacing
    
    context = "\n".join(context_parts)
    
    # Create sophisticated prompt
    prompt = f"""You are a world-class research analyst and strategic consultant with deep expertise in business, entrepreneurship, and academic analysis. Your task is to provide a comprehensive, sophisticated analysis that demonstrates exceptional analytical depth and insight.

## Your Analysis Must Include:

### 1. **Thematic Analysis**
- Identify recurring themes, patterns, and underlying principles
- Extract meta-themes that connect different concepts
- Show how themes evolve or contradict across sources
- Use emojis and clear formatting for visual impact

### 2. **Comparative Framework**
- Compare and contrast different authors' approaches, methodologies, and philosophies
- Highlight where they agree, disagree, or complement each other
- Identify gaps or contradictions in their reasoning
- Show how different perspectives create a more complete picture

### 3. **Strategic Insights**
- Extract practical frameworks and methodologies
- Identify key success factors and risk factors
- Show how concepts apply to real-world scenarios
- Provide actionable insights for decision-making

### 4. **Deep Analysis**
- Go beyond surface-level information to extract underlying principles
- Identify paradoxes, tensions, and nuanced trade-offs
- Show how different factors interact and influence each other
- Demonstrate sophisticated understanding of complex systems

### 5. **Professional Presentation**
- Use clear headings, bullet points, and structured formatting
- Include specific examples and quotes from sources
- Cite sources by filename when making specific points
- Create a compelling narrative that flows logically

## Question: {query}

## Available Sources:
{context}

## Response Requirements:
- **Length**: Provide a comprehensive analysis (aim for 800-1200 words)
- **Structure**: Use clear sections with descriptive headings
- **Depth**: Show sophisticated analytical thinking
- **Examples**: Include specific quotes and examples from sources
- **Insights**: Extract actionable insights and frameworks
- **Comparison**: When multiple sources exist, compare their approaches
- **Meta-analysis**: Identify overarching themes and patterns

## Response Format:
Structure your response with:
1. **Executive Summary** (key insights)
2. **Thematic Analysis** (recurring patterns and themes)
3. **Comparative Framework** (how different sources approach the topic)
4. **Strategic Implications** (practical applications)
5. **Key Takeaways** (actionable insights)

Make this analysis valuable for someone making strategic decisions or conducting research. Demonstrate the depth of insight that comes from sophisticated analysis of multiple sources."""

    return prompt

# Streamlit UI
st.set_page_config(page_title="Knowledge Engine (PDF)", page_icon="📚", layout="wide")

st.title("📚 Sophisticated Knowledge Engine — Deep Analytical Insights")

# Initialize session state
if "selected_collection" not in st.session_state:
    st.session_state.selected_collection = None
if "vs" not in st.session_state:
    st.session_state.vs = None
if "chat" not in st.session_state:
    st.session_state.chat = []

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
                            st.success(f"Selected: {info['topic']}")
                            st.rerun()
                    
                    with col2:
                        if st.button(f"🗑️", key=f"delete_{info['topic']}", help="Delete collection"):
                            if st.session_state.selected_collection == info['topic']:
                                st.session_state.selected_collection = None
                                st.session_state.vs = None
                                st.session_state.chat = []
                            if delete_collection(collection_name):
                                st.success(f"Deleted: {info['topic']}")
                                st.rerun()
        
        # Current selection
        if st.session_state.selected_collection:
            st.success(f"✅ Active: {st.session_state.selected_collection}")
            
            if st.button("🔄 Refresh Collection"):
                st.session_state.vs = get_vector_store(st.session_state.selected_collection)
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
            st.success(f"Created: {new_topic}")
            st.rerun()
        except Exception as e:
            st.error(f"Error creating collection: {str(e)}")

    st.divider()
    
    # Processing settings
    st.header("Processing Settings")
    st.write(f"Chunk size: {CHUNK_SIZE}, overlap: {CHUNK_OVERLAP}")
    st.write("✅ Text cleaning & normalization")
    st.write("✅ NLP entity extraction")
    st.write("✅ Smart sentence-boundary chunking")
    st.write("✅ Keyword extraction")
    st.write("🧠 **Sophisticated analysis & insights**")

    st.header("Status")
    if OPENAI_API_KEY:
        st.success("OpenAI key detected")
    else:
        st.error("Missing OPENAI_API_KEY")

# Main content area
if st.session_state.selected_collection:
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
            status_text.text(f"Processing {f.name} with NLP...")
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
    st.subheader("🧠 Sophisticated Analysis & Insights")
    st.caption("Ask complex questions and get deep, analytical responses with thematic insights and comparative analysis")

    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    query = st.chat_input("Ask a sophisticated question about this topic")
    if query:
        st.session_state.chat.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
        with st.chat_message("assistant"):
            with st.spinner("🧠 Conducting sophisticated analysis..."):
                try:
                    # Intelligent search with more results
                    docs = intelligent_search(st.session_state.vs, query, k=12)
                    
                    # Create sophisticated prompt
                    sophisticated_prompt = create_sophisticated_prompt(query, docs)
                    
                    # Generate with GPT-4 for sophisticated analysis
                    llm = ChatOpenAI(
                        model="gpt-4o",  # Use GPT-4 for sophisticated analysis
                        temperature=0.1,  # Low temperature for consistency
                        openai_api_key=OPENAI_API_KEY
                    )
                    
                    resp = llm.invoke(sophisticated_prompt).content
                    st.markdown(resp)
                    
                    # Enhanced sources with analysis
                    with st.expander("📚 Sources & Analysis"):
                        st.write("**Retrieved Sources:**")
                        for i, d in enumerate(docs, 1):
                            fname = d.metadata.get("file_name", "unknown")
                            entities = d.metadata.get("entities", "")
                            keywords = d.metadata.get("keywords", "")
                            st.write(f"**{i}. {fname}**")
                            if entities:
                                st.write(f"   Entities: {entities}")
                            if keywords:
                                st.write(f"   Keywords: {keywords}")
                            st.write(f"   Content preview: {d.page_content[:300]}...")
                            st.write("---")
                    
                    st.session_state.chat.append({"role": "assistant", "content": resp})
                    
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
                        st.rerun()

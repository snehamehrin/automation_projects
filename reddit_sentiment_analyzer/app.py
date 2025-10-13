"""
Streamlit Web UI for Reddit Sentiment Analyzer
Allows running individual steps of the analysis pipeline
"""

import streamlit as st
import asyncio
from typing import List, Dict, Any
from modules.brand_selector import BrandSelector
from modules.google_search import GoogleSearcher
from modules.reddit_scraper import RedditScraper
from modules.data_processor import DataProcessor
from modules.analysis import Analyzer
from utils.logger import setup_logger

logger = setup_logger()

st.set_page_config(
    page_title="Reddit Sentiment Analyzer",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'prospects' not in st.session_state:
    st.session_state.prospects = []
if 'selected_prospect' not in st.session_state:
    st.session_state.selected_prospect = None
if 'reddit_urls' not in st.session_state:
    st.session_state.reddit_urls = []
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = []
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

# Title
st.title("🔍 Reddit Sentiment Analyzer")
st.markdown("Run brand sentiment analysis step-by-step")

# Sidebar for navigation
st.sidebar.title("Pipeline Steps")
step = st.sidebar.radio(
    "Select Step",
    ["1. Brand Selection", "2. Search Reddit URLs", "3. Scrape Posts & Comments", "4. Process Data", "5. Run Analysis"]
)

# Step 1: Brand Selection
if step == "1. Brand Selection":
    st.header("Step 1: Brand Selection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Load All Prospects")
        if st.button("Load Prospects from Database"):
            with st.spinner("Loading prospects..."):
                try:
                    selector = BrandSelector()
                    prospects = asyncio.run(selector.get_all_prospects())
                    st.session_state.prospects = prospects
                    st.success(f"Loaded {len(prospects)} prospects")
                except Exception as e:
                    st.error(f"Error loading prospects: {str(e)}")
        
        if st.session_state.prospects:
            st.dataframe(
                st.session_state.prospects,
                use_container_width=True
            )
    
    with col2:
        st.subheader("Select or Create Prospect")
        
        option = st.radio("Choose action", ["Select existing", "Create new"])
        
        if option == "Select existing" and st.session_state.prospects:
            selected_brand = st.selectbox(
                "Select Brand",
                options=[p['brand_name'] for p in st.session_state.prospects]
            )
            if st.button("Select This Brand"):
                st.session_state.selected_prospect = next(
                    p for p in st.session_state.prospects 
                    if p['brand_name'] == selected_brand
                )
                st.success(f"Selected: {selected_brand}")
        
        elif option == "Create new":
            brand_name = st.text_input("Brand Name")
            if st.button("Create Prospect") and brand_name:
                with st.spinner("Creating prospect..."):
                    try:
                        selector = BrandSelector()
                        prospect = asyncio.run(selector.get_or_create_prospect(brand_name))
                        st.session_state.selected_prospect = prospect
                        st.success(f"Created: {brand_name}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    if st.session_state.selected_prospect:
        st.info(f"**Current Selection:** {st.session_state.selected_prospect['brand_name']}")

# Step 2: Search Reddit URLs
elif step == "2. Search Reddit URLs":
    st.header("Step 2: Search Reddit URLs")
    
    if not st.session_state.selected_prospect:
        st.warning("⚠️ Please select a prospect in Step 1 first")
    else:
        prospect = st.session_state.selected_prospect
        st.info(f"**Searching for:** {prospect['brand_name']}")
        
        if st.button("Search Google for Reddit URLs"):
            with st.spinner("Searching..."):
                try:
                    searcher = GoogleSearcher()
                    reddit_urls = asyncio.run(
                        searcher.search_reddit_urls(
                            prospect['brand_name'],
                            prospect.get('industry_category', '')
                        )
                    )
                    
                    # Store URLs in database
                    asyncio.run(
                        searcher.update_prospect_urls(
                            prospect['id'],
                            reddit_urls,
                            prospect['brand_name']
                        )
                    )
                    
                    st.session_state.reddit_urls = reddit_urls
                    st.success(f"Found {len(reddit_urls)} Reddit URLs")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        if st.session_state.reddit_urls:
            st.subheader(f"Found {len(st.session_state.reddit_urls)} URLs")
            for i, url_info in enumerate(st.session_state.reddit_urls, 1):
                url = url_info.get('url', '') if isinstance(url_info, dict) else url_info
                title = url_info.get('title', 'No title') if isinstance(url_info, dict) else 'No title'
                with st.expander(f"{i}. {title}"):
                    st.write(f"**URL:** {url}")
                    if isinstance(url_info, dict) and url_info.get('description'):
                        st.write(f"**Description:** {url_info['description']}")

# Step 3: Scrape Posts & Comments
elif step == "3. Scrape Posts & Comments":
    st.header("Step 3: Scrape Reddit Posts & Comments")
    
    if not st.session_state.selected_prospect:
        st.warning("⚠️ Please select a prospect in Step 1 first")
    elif not st.session_state.reddit_urls:
        st.warning("⚠️ Please search for Reddit URLs in Step 2 first")
    else:
        prospect = st.session_state.selected_prospect
        st.info(f"**Scraping for:** {prospect['brand_name']}")
        st.write(f"**URLs to scrape:** {len(st.session_state.reddit_urls)}")
        
        if st.button("Scrape All URLs"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                scraper = RedditScraper()
                all_data = []
                
                for i, url_info in enumerate(st.session_state.reddit_urls):
                    url = url_info.get('url', '') if isinstance(url_info, dict) else url_info
                    status_text.text(f"Scraping {i+1}/{len(st.session_state.reddit_urls)}: {url}")
                    
                    try:
                        data = asyncio.run(
                            scraper.scrape_all_urls(
                                [url_info],
                                prospect['brand_name'],
                                prospect['id']
                            )
                        )
                        all_data.extend(data)
                    except Exception as e:
                        st.warning(f"Error scraping {url}: {str(e)}")
                    
                    progress_bar.progress((i + 1) / len(st.session_state.reddit_urls))
                
                st.session_state.scraped_data = all_data
                status_text.text("Scraping complete!")
                st.success(f"Scraped {len(all_data)} posts/comments")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        if st.session_state.scraped_data:
            st.subheader(f"Scraped {len(st.session_state.scraped_data)} items")
            
            # Show sample
            with st.expander("View Sample Data"):
                st.json(st.session_state.scraped_data[:3])

# Step 4: Process Data
elif step == "4. Process Data":
    st.header("Step 4: Process & Clean Data")
    
    if not st.session_state.selected_prospect:
        st.warning("⚠️ Please select a prospect in Step 1 first")
    elif not st.session_state.scraped_data:
        st.warning("⚠️ Please scrape data in Step 3 first")
    else:
        prospect = st.session_state.selected_prospect
        st.info(f"**Processing data for:** {prospect['brand_name']}")
        st.write(f"**Raw items:** {len(st.session_state.scraped_data)}")
        
        if st.button("Process & Clean Data"):
            with st.spinner("Processing..."):
                try:
                    processor = DataProcessor()
                    cleaned_data = asyncio.run(
                        processor.process_data(
                            st.session_state.scraped_data,
                            prospect['brand_name'],
                            prospect['id']
                        )
                    )
                    st.session_state.cleaned_data = cleaned_data
                    st.success(f"Processed {len(cleaned_data)} valid items")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        if hasattr(st.session_state, 'cleaned_data'):
            st.subheader(f"Cleaned {len(st.session_state.cleaned_data)} items")
            
            # Show stats
            col1, col2, col3 = st.columns(3)
            with col1:
                posts = len([d for d in st.session_state.cleaned_data if d.get('data_type') == 'post'])
                st.metric("Posts", posts)
            with col2:
                comments = len([d for d in st.session_state.cleaned_data if d.get('data_type') == 'comment'])
                st.metric("Comments", comments)
            with col3:
                st.metric("Total Items", len(st.session_state.cleaned_data))

# Step 5: Run Analysis
elif step == "5. Run Analysis":
    st.header("Step 5: AI-Powered Analysis")
    
    if not st.session_state.selected_prospect:
        st.warning("⚠️ Please select a prospect in Step 1 first")
    elif not hasattr(st.session_state, 'cleaned_data'):
        st.warning("⚠️ Please process data in Step 4 first")
    else:
        prospect = st.session_state.selected_prospect
        st.info(f"**Analyzing:** {prospect['brand_name']}")
        st.write(f"**Items to analyze:** {len(st.session_state.cleaned_data)}")
        
        if st.button("Run AI Analysis"):
            with st.spinner("Analyzing with OpenAI..."):
                try:
                    analyzer = Analyzer()
                    result = asyncio.run(
                        analyzer.analyze(
                            st.session_state.cleaned_data,
                            prospect['brand_name'],
                            prospect['id']
                        )
                    )
                    st.session_state.analysis_result = result
                    st.success("Analysis complete!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        if st.session_state.analysis_result:
            result = st.session_state.analysis_result
            
            st.subheader("Analysis Results")
            
            # Key Insight
            st.markdown("### 💡 Key Insight")
            st.info(result.get('key_insight', 'No insight available'))
            
            # Sentiment
            if 'overall_sentiment' in result:
                st.markdown("### 😊 Overall Sentiment")
                sentiment = result['overall_sentiment']
                if sentiment == 'positive':
                    st.success(f"**{sentiment.upper()}**")
                elif sentiment == 'negative':
                    st.error(f"**{sentiment.upper()}**")
                else:
                    st.warning(f"**{sentiment.upper()}**")
            
            # Full analysis
            with st.expander("View Full Analysis"):
                st.json(result)

# Status bar at bottom
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    if st.session_state.selected_prospect:
        st.success(f"✅ Prospect: {st.session_state.selected_prospect['brand_name']}")
    else:
        st.info("ℹ️ No prospect selected")

with col2:
    if st.session_state.reddit_urls:
        st.success(f"✅ URLs: {len(st.session_state.reddit_urls)}")
    else:
        st.info("ℹ️ No URLs found")

with col3:
    if st.session_state.analysis_result:
        st.success("✅ Analysis complete")
    else:
        st.info("ℹ️ No analysis yet")

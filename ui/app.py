"""
Amazon Product Research - Streamlit UI

Web interface for comparing Amazon bestsellers across different markets.
"""

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'execution'))

from amazon_scraper import (
    MARKETS,
    CATEGORY_URLS,
    scrape_bestsellers,
    scrape_market,
    test_connection
)
from product_comparator import (
    compare_markets,
    opportunities_to_csv_rows
)
from ai_analyzer import analyze_opportunities, format_products_for_analysis

# Cached scraping function (cache for 1 hour to avoid repeated API calls)
@st.cache_data(ttl=3600, show_spinner=False)
def cached_scrape_bestsellers(url: str, max_results: int, subcategories: int):
    """Cached wrapper for scrape_bestsellers to avoid repeated API calls."""
    return scrape_bestsellers(url, max_results=max_results, subcategories=subcategories)

# Page config
st.set_page_config(
    page_title="Amazon Product Research",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    /* Global Settings */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        color: #e0e0e0;
    }
    
    /* Main Background */
    .stApp {
        background-color: #0e1117; /* Standard clean dark background */
        background-image: none;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
        box-shadow: none;
    }
    
    /* Headings - Clean White */
    h1, h2, h3 {
        font-weight: 600 !important;
        color: #ffffff !important;
        background: none;
        -webkit-text-fill-color: initial;
        letter-spacing: -0.5px;
        text-transform: none;
        text-shadow: none;
    }
    
    /* Paragraphs */
    p, .stMarkdown {
        color: #a0a0a0;
        font-size: 1rem;
        font-weight: 400;
    }

    /* Buttons - Minimalist White/Grey */
    .stButton button {
        background-color: #f0f0f0;
        color: #0e1117;
        border: 1px solid #f0f0f0;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        text-transform: none;
        letter-spacing: normal;
        box-shadow: none;
        transition: background-color 0.2s;
        clip-path: none;
    }
    .stButton button:hover {
        background-color: #ffffff;
        border-color: #ffffff;
        transform: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton button:active {
        background-color: #e0e0e0;
    }
    .stButton button:disabled {
        background-color: #2b313a;
        border-color: #2b313a;
        color: #6e7681;
    }

    /* Inputs - Clean Dark */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #0d1117;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
        border-color: #58a6ff;
        box-shadow: none;
    }
    
    /* Checkboxes */
    .stCheckbox label span[role="checkbox"][aria-checked="true"] {
        background-color: #58a6ff !important;
        border-color: #58a6ff !important;
    }

    /* Cards / Metrics */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 1rem;
        border-left: none; /* Removed colored accents */
    }
    div[data-testid="stMetricLabel"] {
        color: #8b949e;
        font-weight: 400;
        text-transform: none;
        font-size: 0.875rem;
    }
    div[data-testid="stMetricValue"] {
        color: #f0f6fc;
        font-weight: 600;
        text-shadow: none;
    }

    /* Sliders - Standard Blue/Grey Accent */
    div[data-baseweb="slider"] {
        padding-top: 1.5rem !important;
    }
    div[data-baseweb="slider"] div[role="slider"] {
        background-color: #58a6ff !important;
        box-shadow: none;
    }
    div[data-baseweb="slider"] div[data-testid="stTickBar"] div {
        background-color: #30363d;
    }
    div[data-baseweb="slider"] div {
        background-color: transparent !important;
    }
    div[data-baseweb="slider"] div[data-testid="stSliderTrack"] {
        background-color: #30363d !important;
    }
    /* Value Labels */
    .stSlider [data-testid="stMarkdownContainer"] p {
        color: #c9d1d9 !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        text-shadow: none;
    }

    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: #58a6ff; /* Clean Blue */
        box-shadow: none;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #161b22;
        border: 1px solid #30363d;
        color: #c9d1d9;
        border-radius: 6px;
    }
    .streamlit-expanderContent {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-top: none;
        border-radius: 0 0 6px 6px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        border-bottom: 1px solid #30363d;
    }
    .stTabs [data-baseweb="tab"] {
        color: #8b949e;
        font-weight: 500;
        background-color: transparent;
        text-transform: none;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        color: #58a6ff !important;
        border-bottom: 2px solid #58a6ff !important;
        background-color: transparent !important;
    }
    
    /* Links */
    a {
        color: #58a6ff !important;
        text-decoration: none;
        font-weight: 400;
        text-shadow: none;
    }
    a:hover {
        text-decoration: underline;
        text-shadow: none;
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.title("🔍 Amazon Product Research")
    st.markdown("Find product opportunities across Amazon markets")
    
    # Initialize session state for caching results
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'analysis_params' not in st.session_state:
        st.session_state.analysis_params = None
    if 'ai_analysis' not in st.session_state:
        st.session_state.ai_analysis = None
    if 'analysis_params' not in st.session_state:
        st.session_state.analysis_params = None
    
    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Market selection
        st.subheader("🌍 Markets")
        
        market_options = {
            code: f"{info['flag']} {info['name']}" 
            for code, info in MARKETS.items()
        }
        

        
        # Append Universal option if not in dict (it's a hack to show it in selectbox)
        # Actually easier to just add it to options dict temporarily or handle in code
        # Let's handle it by adding a literal option
        
        market_options_with_univ = market_options.copy()
        market_options_with_univ['universal'] = "🌐 Custom Site (AI Agent)"
        
        source_market = st.selectbox(
            "Source Market (find products here)",
            options=list(market_options_with_univ.keys()),
            format_func=lambda x: market_options_with_univ[x],
            index=1  # Default: Japan
        )
        
        target_market = st.selectbox(
            "Target Market (sell products here)",
            options=list(market_options.keys()),
            format_func=lambda x: market_options[x],
            index=0  # Default: USA
        )
        
        if source_market == target_market:
            st.warning("⚠️ Source and target markets should be different")
        
        st.divider()
        
        # Parameters
        st.subheader("📊 Parameters")
        
        max_results = st.slider(
            "Scan Top N Products (List Only)",
            min_value=5,
            max_value=100,
            value=10,
            step=5,
            help="How many items to scan from the bestseller list. Higher = more data but slower."
        )
        
        min_reviews = st.slider(
            "Min reviews (source market)",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100
        )
        
        include_subcategories = st.checkbox(
            "Include subcategories",
            value=False,
            help="If checked, also scrapes products from subcategories (more results, but less precise)"
        )
        
        st.divider()
        
        # API Status
        st.subheader("🔌 API Status")
        if st.button("Test Connection"):
            with st.spinner("Testing..."):
                try:
                    if test_connection():
                        st.success("✅ Connected!")
                    else:
                        st.error("❌ Connection failed")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    
        # Debug / Universal Source Info
        if source_market == 'universal':
            st.info("ℹ️ You are using the Universal Agent (AliExpress/Other). Product discovery will be slower (AI-driven).")
    
    # Main content - Tabs
    tab1, tab2 = st.tabs(["📊 Market Analysis", "🔍 Product Search"])
    
    with tab1:
        st.header("📊 Market Comparison")
        
        # Dynamic Header based on Source
        if source_market == 'universal':
            st.markdown(f"Finding bestsellers on **AliExpress** to compare with **{market_options.get(target_market, target_market)}**")
            
            # Universal Source Inputs
            st.subheader("🌐 Universal Source Configuration")
            st.info("ℹ️ Categories are automatically mapped to AliExpress. Selected categories will be scraped from BOTH AliExpress (Source) and Amazon (Target) for direct comparison.")
            
            univ_col1, univ_col2 = st.columns([2, 1])
            with univ_col1:
                 # Optional: Allow Manual Override
                 use_manual_url = st.checkbox("Use Custom URL instead of Category Map", value=False)
                 
            with univ_col2:
                 agent_prompt = st.text_input("Refinement Prompt (Optional)", value="Find top trending items", help="Filter logic for the AI Agent")

            if use_manual_url:
                target_site_url = st.text_input("Custom Target URL", value="https://www.aliexpress.com")
            else:
                target_site_url = None # Will be derived from category loop
                 
            # Shared Category Selection
            st.subheader("📦 Select Categories (Source & Target)")
            
            category_names = {
                "home-garden": "🏠 Home & Kitchen",
                "pet-supplies": "🐾 Pet Supplies",
                "office-products": "📎 Office Products",
                "sports-outdoors": "⚽ Sports & Outdoors",
                "toys-games": "🎮 Toys & Games",
                "adult": "🔞 Adult (18+)"
            }
            
            cols = st.columns(3)
            selected_categories = []
            
            for i, (cat_id, cat_name) in enumerate(category_names.items()):
                with cols[i % 3]:
                    if st.checkbox(cat_name, value=(i == 0), key=f"univ_cat_{cat_id}"):
                        selected_categories.append(cat_id)

            if not selected_categories:
                st.warning("Please select at least one category.")
                
        else:
            st.markdown(f"Finding products popular in **{market_options.get(source_market, source_market)}** but not in **{market_options.get(target_market, target_market)}**")
            
            # Category selection (Only for Standard Markets)
            st.subheader("📦 Select Categories")
            
            category_names = {
                "home-garden": "🏠 Home & Kitchen",
                "pet-supplies": "🐾 Pet Supplies",
                "office-products": "📎 Office Products",
                "sports-outdoors": "⚽ Sports & Outdoors",
                "toys-games": "🎮 Toys & Games",
                "adult": "🔞 Adult (18+)"
            }
            
            cols = st.columns(3)
            selected_categories = []
            
            for i, (cat_id, cat_name) in enumerate(category_names.items()):
                with cols[i % 3]:
                    if st.checkbox(cat_name, value=(i == 0), key=f"cat_{cat_id}"):
                        selected_categories.append(cat_id)
            
            if not selected_categories:
                st.warning("Please select at least one category")
        
        # Run button
        st.divider()
        
        # Logic for Universal vs Standard Validation
        is_ready = False
        if source_market == 'universal':
             is_ready = len(selected_categories) > 0 and (not use_manual_url or target_site_url)
        else:
             is_ready = len(selected_categories) > 0

        if st.button("🚀 Run Analysis", type="primary", disabled=not is_ready):
            if source_market == target_market:
                st.error("Please select different source and target markets")
            else:
                # Pass universal params if applicable
                universal_params = {}
                if source_market == 'universal':
                    universal_params = {
                        "prompt": agent_prompt,
                        "use_manual_url": use_manual_url,
                        "manual_url": target_site_url if use_manual_url else None
                    }
                    # We utilize the same 'selected_categories' list for the loop!
 
                result = run_analysis(
                    source_market=source_market,
                    target_market=target_market,
                    categories=selected_categories,
                    max_results=max_results,
                    min_reviews=min_reviews,
                    market_options=market_options,
                    subcategories=1 if include_subcategories else 0,
                    universal_params=universal_params
                )
                # Cache results in session
                if result:
                    st.session_state.analysis_results = result
                    st.session_state.analysis_params = {
                        'source': market_options.get(source_market, "🌐 Custom Site (AI Agent)"),
                        'target': market_options.get(target_market, target_market),
                        'source_code': source_market,
                        'target_code': target_market,
                        'time': datetime.now().strftime('%H:%M:%S')
                    }
        
        # Show cached results if available (with unique key prefix)
        if st.session_state.analysis_results:
            params = st.session_state.analysis_params
            st.success(f"📊 Showing cached results from {params['time']} ({params['source']} → {params['target']})")
            display_results(
                st.session_state.analysis_results,
                params.get('source_code', source_market),
                params.get('target_code', target_market),
                market_options,
                key_prefix="cached_"
            )
            
            # AI Analysis Section
            st.divider()
            st.subheader("🤖 AI Анализ продуктов")
            st.markdown("Получите профессиональный анализ от AI: культурные различия, рекомендации по продажам, потенциальные риски.")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🧠 Запустить AI анализ", type="primary", key="ai_analysis_btn"):
                    with st.spinner("🔄 AI анализирует продукты... (30-60 сек)"):
                        try:
                            # Get country names from market codes
                            # Handle 'universal' (AliExpress) which is not in MARKETS
                            if params['source_code'] == 'universal':
                                source_country = "China (AliExpress)"
                            else:
                                source_country = MARKETS[params['source_code']]['name']
                            target_country = MARKETS[params['target_code']]['name']
                            
                            ai_result = analyze_opportunities(
                                opportunities=st.session_state.analysis_results,
                                source_market=params['source_code'].upper(),
                                target_market=params['target_code'].upper(),
                                source_country=source_country,
                                target_country=target_country
                            )
                            st.session_state.ai_analysis = ai_result
                        except Exception as e:
                            st.error(f"❌ Ошибка AI анализа: {e}")
            
            # Display AI analysis if available
            if st.session_state.ai_analysis:
                st.markdown("---")
                st.markdown(st.session_state.ai_analysis)
                
                # === AI CHAT INTERFACE ===
                st.markdown("---")
                st.subheader("💬 Обсудить с AI")
                st.markdown("Задайте вопросы о продуктах, попросите детали или обсудите стратегию")
                
                # Initialize chat history if not exists
                if 'chat_messages' not in st.session_state:
                    st.session_state.chat_messages = []
                
                # Display chat history
                for message in st.session_state.chat_messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
                
                # Chat input
                if user_message := st.chat_input("Напишите вопрос о продуктах..."):
                    # Add user message to history
                    st.session_state.chat_messages.append({"role": "user", "content": user_message})
                    
                    # Display user message
                    with st.chat_message("user"):
                        st.markdown(user_message)
                    
                    # Generate AI response
                    with st.chat_message("assistant"):
                        with st.spinner("🤔 Думаю..."):
                            try:
                                from openai import OpenAI
                                import os
                                
                                # Get API key
                                api_key = None
                                try:
                                    if "OPENAI_API_KEY" in st.secrets:
                                        api_key = st.secrets["OPENAI_API_KEY"]
                                except:
                                    pass
                                if not api_key:
                                    api_key = os.getenv("OPENAI_API_KEY")
                                
                                if not api_key:
                                    st.error("OpenAI API key not found")
                                else:
                                    client = OpenAI(api_key=api_key)
                                    
                                    # Build context from analysis results
                                    products_context = format_products_for_analysis(
                                        st.session_state.analysis_results, 
                                        params.get('source_code', 'source'), 
                                        params.get('target_code', 'target')
                                    )
                                    
                                    # Build messages for API
                                    messages = [
                                        {
                                            "role": "system", 
                                            "content": f"""Ты эксперт по Amazon FBA и арбитражу. 
У тебя есть данные о продуктах и предыдущий анализ.

КОНТЕКСТ ПРОДУКТОВ:
{products_context[:3000]}

ПРЕДЫДУЩИЙ АНАЛИЗ:
{st.session_state.ai_analysis[:2000]}

Отвечай на русском языке. Будь конкретным, ссылайся на реальные продукты из данных.
Если спрашивают о конкретном продукте — дай детальный анализ с расчётами."""
                                        }
                                    ]
                                    
                                    # Add chat history
                                    for msg in st.session_state.chat_messages[-10:]:  # Last 10 messages
                                        messages.append({"role": msg["role"], "content": msg["content"]})
                                    
                                    response = client.chat.completions.create(
                                        model="gpt-4o",
                                        messages=messages,
                                        temperature=0.7,
                                        max_tokens=2000
                                    )
                                    
                                    ai_response = response.choices[0].message.content
                                    st.markdown(ai_response)
                                    
                                    # Add AI response to history
                                    st.session_state.chat_messages.append({"role": "assistant", "content": ai_response})
                                    
                                    # Rerun to properly display conversation
                                    st.rerun()
                                    
                            except Exception as e:
                                st.error(f"Ошибка AI: {e}")
                
                # Clear chat button
                if st.session_state.chat_messages:
                    if st.button("🗑️ Очистить чат", key="clear_chat_btn"):
                        st.session_state.chat_messages = []
                        st.rerun()
            
            st.divider()
            
            # Clear cache button
            if st.button("🗑️ Clear cached results", key="clear_cache_btn"):
                st.session_state.analysis_results = None
                st.session_state.analysis_params = None
                st.session_state.ai_analysis = None
                st.session_state.chat_messages = []
                st.rerun()
    
    with tab2:
        render_product_search(market_options)


def render_product_search(market_options):
    """Render the Product Search tab."""
    st.header("🔍 Product Search")
    st.markdown("Search for a specific product across multiple Amazon markets")
    
    # Search input
    search_query = st.text_input(
        "Product name or keywords",
        placeholder="e.g., wireless earbuds, rice cooker, yoga mat...",
        key="product_search_input"
    )
    
    # Market selection for search
    st.subheader("🌍 Select markets to search")
    
    search_markets = []
    cols = st.columns(4)
    for i, (code, info) in enumerate(MARKETS.items()):
        with cols[i % 4]:
            if st.checkbox(f"{info['flag']} {info['name']}", value=(code in ['us', 'jp']), key=f"search_market_{code}"):
                search_markets.append(code)
    
    # Search button
    if st.button("🔎 Search", type="primary", disabled=not search_query or not search_markets, key="search_btn"):
        search_product(search_query, search_markets, market_options)


def search_product(query, markets, market_options):
    """Search for a product across selected markets."""
    st.divider()
    
    progress = st.progress(0)
    status = st.empty()
    
    results = {}
    
    for i, market in enumerate(markets):
        status.text(f"🔄 Searching in {market_options[market]}...")
        progress.progress((i + 1) / len(markets))
        
        # For now, we'll use the bestsellers API and filter by name
        # A proper implementation would use Amazon's search API
        try:
            # Search in Home & Kitchen category as proxy
            url = CATEGORY_URLS.get('home-garden', {}).get(market)
            if url:
                products = cached_scrape_bestsellers(url, max_results=50, subcategories=1)
                
                # Filter products that match query
                matching = [
                    p for p in products 
                    if query.lower() in p.get('name', '').lower()
                ]
                results[market] = {
                    'products': matching[:10],
                    'total_found': len(matching)
                }
        except Exception as e:
            results[market] = {'products': [], 'error': str(e)}
    
    progress.progress(100)
    status.text("✅ Search complete!")
    
    # Display results
    st.subheader(f"📊 Results for '{query}'")
    
    if not any(r.get('products') for r in results.values()):
        st.warning("No products found matching your search. Try different keywords or categories.")
        st.info("💡 Tip: Product Search currently searches within bestseller lists. For broader searches, try more generic terms.")
        return
    
    # Show results by market
    for market, data in results.items():
        products = data.get('products', [])
        
        with st.expander(f"{market_options[market]} - {len(products)} found", expanded=len(products) > 0):
            if products:
                for p in products:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{p.get('name', 'Unknown')[:80]}...**")
                        st.caption(f"⭐ {p.get('stars', 'N/A')} | 💬 {p.get('reviewsCount', 0):,} reviews")
                    with col2:
                        price = p.get('price', {})
                        st.write(f"{price.get('currency', '')}{price.get('value', 'N/A')}")
                        if p.get('url'):
                            st.link_button("View", p['url'], use_container_width=True)
            elif data.get('error'):
                st.error(f"Error: {data['error']}")
            else:
                st.info("No matching products found")


def run_analysis(source_market, target_market, categories, max_results, min_reviews, market_options, subcategories=0, universal_params=None):
    """Run the market comparison analysis. Returns opportunities dict."""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Scrape source market
        market_name = market_options.get(source_market, "Universal Source")
        status_text.text(f"🔄 Scraping {market_name}...")
        progress_bar.progress(10)
        
        # DEBUG: Show values in UI to trace execution path
        st.warning(f"🔧 DEBUG: source_market='{source_market}', universal_params={bool(universal_params)}, condition={source_market == 'universal' and bool(universal_params)}")
        
        if source_market == 'universal' and universal_params:
            st.success("✅ Entering UNIVERSAL branch (Firecrawl)")
            # Universal Source Flow
            # Lazy import to avoid circular dependency
            from universal_adapter import UniversalAdapter
            
            # DEBUG: Show adapter initialization
            st.info("🔧 DEBUG: Initializing UniversalAdapter...")
            try:
                adapter = UniversalAdapter()
                st.success("✅ UniversalAdapter initialized successfully")
            except Exception as init_error:
                import traceback
                st.error(f"❌ UniversalAdapter INIT FAILED: {init_error}")
                st.code(traceback.format_exc())
                raise init_error
            
            source_data = {}
            
            for i, category in enumerate(categories):
                 status_text.text(f"🤖 Agent Scraping {category} from AliExpress...")
                 
                 # Determine URL
                 if universal_params.get("use_manual_url") and universal_params.get("manual_url"):
                     # Use the same manual URL for all categories (user override)
                     target_url = universal_params["manual_url"]
                 else:
                     # Use mapping
                     target_url = adapter.get_category_url(category)
                 
                 # DEBUG: Show URL being called
                 st.info(f"🔗 DEBUG: Calling Firecrawl with URL: {target_url}")
                 
                 try:
                     st.info("🔄 DEBUG: Starting scrape_products call...")
                     products = adapter.scrape_products(
                        url=target_url,
                        prompt=universal_params['prompt'],
                        limit=max_results
                     )
                     st.success(f"✅ Firecrawl returned {len(products)} products for {category}")
                     
                     # Extra debug: show first product if any
                     if products:
                         st.info(f"🔍 First product: {products[0].get('name', 'N/A')[:50]}")
                 except Exception as fc_error:
                     import traceback
                     st.error(f"❌ Firecrawl FAILED: {fc_error}")
                     st.code(traceback.format_exc())
                     products = []
                 
                 source_data[category] = products
                 progress_bar.progress(10 + int(30 * (i + 1) / len(categories)))
            
        else:
            # Standard Amazon Flow
            source_data = {}
            for i, category in enumerate(categories):
                market_name = market_options.get(source_market, source_market)
                status_text.text(f"🔄 Scraping {category} from {market_name}...")
                url = CATEGORY_URLS[category][source_market]
                products = cached_scrape_bestsellers(url, max_results=max_results, subcategories=subcategories)
                source_data[category] = products
                progress_bar.progress(10 + int(30 * (i + 1) / len(categories)))
        
        # Step 2: Scrape target market
        status_text.text(f"🔄 Scraping {market_options[target_market]}...")
        
        target_data = {}
        for i, category in enumerate(categories):
            status_text.text(f"🔄 Scraping {category} from {market_options[target_market]}...")
            url = CATEGORY_URLS[category][target_market]
            products = cached_scrape_bestsellers(url, max_results=max_results, subcategories=subcategories)
            target_data[category] = products
            progress_bar.progress(40 + int(30 * (i + 1) / len(categories)))
        
        # Step 3: Compare
        status_text.text("🔍 Analyzing opportunities...")
        progress_bar.progress(80)
        
        # Detect if we are in universal mode
        is_universal = True if (universal_params and 'prompt' in universal_params) else False
        
        opportunities = compare_markets(
            us_data=target_data,
            jp_data=source_data,
            min_reviews=min_reviews,
            universal_mode=is_universal
        )
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        
        # Display results
        display_results(opportunities, source_market, target_market, market_options, key_prefix="new_")
        
        return opportunities  # Return for caching
        
    except Exception as e:
        st.error(f"❌ Error during analysis: {e}")
        return None


def display_results(opportunities, source_market, target_market, market_options, key_prefix=""):
    """Display analysis results with unique key prefix to avoid duplicate element IDs."""
    
    total_opps = sum(len(opps) for opps in opportunities.values())
    
    st.divider()
    st.header(f"🎯 Found {total_opps} Opportunities")
    
    if total_opps == 0:
        st.info("No opportunities found with current settings. Try lowering the minimum reviews threshold.")
        return
    
    # Convert to DataFrame for display
    rows = opportunities_to_csv_rows(opportunities)
    df = pd.DataFrame(rows)
    
    # Rename columns for display
    df = df.rename(columns={
        'category': 'Category',
        'opportunity_score': 'Score',
        'jp_name': 'Product Name',
        'jp_reviews': 'Reviews',
        'jp_stars': 'Rating',
        'jp_price': 'Price',
        'jp_url': 'URL',
        'jp_thumbnail': 'Thumbnail',
        'reason': 'Reason'
    })
    
    # Sort by score
    df = df.sort_values('Score', ascending=False).reset_index(drop=True)
    
    # Display top opportunities
    st.subheader("🏆 Top Opportunities")
    
    for idx, row in df.head(5).iterrows():
        product_name = row.get('Product Name', 'Unknown')[:60]
        product_url = row.get('URL', '')
        thumbnail_url = row.get('Thumbnail', '')
        
        with st.expander(f"**[{row['Score']:.0f}]** {product_name}...", expanded=(idx == 0)):
            # Show thumbnail if available
            img_col, info_col = st.columns([1, 3])
            
            with img_col:
                if thumbnail_url:
                    st.image(thumbnail_url, width=120)
                else:
                    st.write("📷 No image")
            
            with info_col:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Reviews", f"{row['Reviews']:,}")
                with col2:
                    st.metric("Rating", f"⭐ {row['Rating']}")
                with col3:
                    st.metric("Price", row['Price'])
            
            st.caption(row['Reason'])
            
            # Add clickable link button
            if product_url:
                st.link_button("🔗 View Product", product_url)
    
    # Full table with clickable links
    st.subheader("📋 All Results")
    
    # Select columns to display
    display_cols = ['Score', 'Category', 'Product Name', 'Reviews', 'Rating', 'Price', 'URL']
    display_cols = [c for c in display_cols if c in df.columns]
    
    # Configure dataframe with clickable URL column
    st.dataframe(
        df[display_cols],
        use_container_width=True,
        column_config={
            "URL": st.column_config.LinkColumn(
                "🔗 Link",
                display_text="Open",
                width="small"
            ),
            "Score": st.column_config.NumberColumn(format="%.0f"),
            "Reviews": st.column_config.NumberColumn(format="%d"),
        }
    )
    
    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"opportunities_{source_market}_to_{target_market}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        key=f"{key_prefix}download_csv"
    )


if __name__ == "__main__":
    main()

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

# Page config
st.set_page_config(
    page_title="Amazon Product Research",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    /* Main Layout & Background */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(18, 28, 45) 0%, rgb(11, 15, 25) 90%);
        color: #E6EAF1;
    }
    
    /* Headers & Text */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #4CAF50, #00C853);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding-bottom: 0.5rem;
    }
    
    p, .stMarkdown {
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        color: #B0B8C8;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: rgb(15, 20, 30);
        border-right: 1px solid rgba(76, 175, 80, 0.1);
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px 0 rgba(76, 175, 80, 0.39);
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(76, 175, 80, 0.23);
        background: linear-gradient(135deg, #66BB6A 0%, #43A047 100%);
    }
    .stButton button:disabled {
        background: #2d3748;
        color: #718096;
    }

    /* Cards / Expanders */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        color: #E2E8F0;
        font-weight: 500;
    }
    .streamlit-expanderContent {
        background-color: rgba(0, 0, 0, 0.2);
        border-radius: 0 0 10px 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: none;
        padding: 1rem;
    }

    /* Metrics styling */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.03);
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(76, 175, 80, 0.1);
        text-align: center;
        transition: 0.3s;
    }
    div[data-testid="stMetric"]:hover {
        background-color: rgba(255, 255, 255, 0.06);
        border-color: rgba(76, 175, 80, 0.3);
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8;
        font-size: 0.9rem;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF;
        font-weight: 700;
        font-size: 1.5rem;
    }

    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #4CAF50, #00E676);
        border-radius: 10px;
    }

    /* Checkboxes & Inputs */
    .stCheckbox label {
        color: #E2E8F0;
    }
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.05);
        color: #FFFFFF;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
    }
    .stTextInput input:focus {
        border-color: #4CAF50;
        box-shadow: 0 0 0 1px #4CAF50;
    }

    /* DataFrame styling */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Dividers */
    hr {
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Custom alerts */
    .stAlert {
        border-radius: 10px;
        background-color: rgba(25, 30, 45, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: rgba(255, 255, 255, 0.03);
        border-radius: 8px 8px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #94A3B8;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(76, 175, 80, 0.1) !important;
        color: #4CAF50 !important;
        border-bottom: 2px solid #4CAF50 !important;
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
    
    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Market selection
        st.subheader("🌍 Markets")
        
        market_options = {
            code: f"{info['flag']} {info['name']}" 
            for code, info in MARKETS.items()
        }
        
        source_market = st.selectbox(
            "Source Market (find products here)",
            options=list(market_options.keys()),
            format_func=lambda x: market_options[x],
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
            "Max products per category",
            min_value=5,
            max_value=50,
            value=20,
            step=5
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
    
    # Main content - Tabs
    tab1, tab2 = st.tabs(["📊 Market Analysis", "🔍 Product Search"])
    
    with tab1:
        st.header("📊 Market Comparison")
        st.markdown(f"Finding products popular in **{market_options[source_market]}** but not in **{market_options[target_market]}**")
        
        # Category selection
        st.subheader("📦 Select Categories")
        
        category_names = {
            "home-garden": "🏠 Home & Kitchen",
            "pet-supplies": "🐾 Pet Supplies",
            "office-products": "📎 Office Products",
            "sports-outdoors": "⚽ Sports & Outdoors",
            "toys-games": "🎮 Toys & Games"
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
        
        if st.button("🚀 Run Analysis", type="primary", disabled=len(selected_categories) == 0):
            if source_market == target_market:
                st.error("Please select different source and target markets")
            else:
                result = run_analysis(
                    source_market=source_market,
                    target_market=target_market,
                    categories=selected_categories,
                    max_results=max_results,
                    min_reviews=min_reviews,
                    market_options=market_options,
                    subcategories=1 if include_subcategories else 0
                )
                # Cache results in session
                if result:
                    st.session_state.analysis_results = result
                    st.session_state.analysis_params = {
                        'source': market_options[source_market],
                        'target': market_options[target_market],
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
            
            # Clear cache button
            if st.button("🗑️ Clear cached results", key="clear_cache_btn"):
                st.session_state.analysis_results = None
                st.session_state.analysis_params = None
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
                products = scrape_bestsellers(url, max_results=50, subcategories=1)
                
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


def run_analysis(source_market, target_market, categories, max_results, min_reviews, market_options, subcategories=0):
    """Run the market comparison analysis. Returns opportunities dict."""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Scrape source market
        status_text.text(f"🔄 Scraping {market_options[source_market]}...")
        progress_bar.progress(10)
        
        source_data = {}
        for i, category in enumerate(categories):
            status_text.text(f"🔄 Scraping {category} from {market_options[source_market]}...")
            url = CATEGORY_URLS[category][source_market]
            products = scrape_bestsellers(url, max_results=max_results, subcategories=subcategories)
            source_data[category] = products
            progress_bar.progress(10 + int(30 * (i + 1) / len(categories)))
        
        # Step 2: Scrape target market
        status_text.text(f"🔄 Scraping {market_options[target_market]}...")
        
        target_data = {}
        for i, category in enumerate(categories):
            status_text.text(f"🔄 Scraping {category} from {market_options[target_market]}...")
            url = CATEGORY_URLS[category][target_market]
            products = scrape_bestsellers(url, max_results=max_results, subcategories=subcategories)
            target_data[category] = products
            progress_bar.progress(40 + int(30 * (i + 1) / len(categories)))
        
        # Step 3: Compare
        status_text.text("🔍 Analyzing opportunities...")
        progress_bar.progress(80)
        
        opportunities = compare_markets(
            us_data=target_data,
            jp_data=source_data,
            min_reviews=min_reviews
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
        'reason': 'Reason'
    })
    
    # Sort by score
    df = df.sort_values('Score', ascending=False).reset_index(drop=True)
    
    # Display top opportunities
    st.subheader("🏆 Top Opportunities")
    
    for idx, row in df.head(5).iterrows():
        product_name = row.get('Product Name', 'Unknown')[:60]
        product_url = row.get('URL', '')
        
        with st.expander(f"**[{row['Score']:.0f}]** {product_name}...", expanded=(idx == 0), key=f"{key_prefix}exp_{idx}"):
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
                st.link_button("🔗 View on Amazon", product_url, key=f"{key_prefix}link_{idx}")
    
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
        mime="text/csv"
    )


if __name__ == "__main__":
    main()

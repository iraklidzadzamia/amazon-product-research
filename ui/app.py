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
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    .opportunity-score {
        font-size: 24px;
        font-weight: bold;
        color: #4CAF50;
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
                        'time': datetime.now().strftime('%H:%M:%S')
                    }
        
        # Show cached results if available
        if st.session_state.analysis_results:
            params = st.session_state.analysis_params
            st.success(f"📊 Showing cached results from {params['time']} ({params['source']} → {params['target']})")
            display_results(
                st.session_state.analysis_results,
                source_market, target_market, market_options
            )
            
            # Clear cache button
            if st.button("🗑️ Clear cached results"):
                st.session_state.analysis_results = None
                st.session_state.analysis_params = None
                st.rerun()
    
    with tab2:
        st.header("🔍 Product Search")
        st.markdown("*Coming soon!*")
        st.info("This feature will allow you to search for a specific product across all markets.")


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
        display_results(opportunities, source_market, target_market, market_options)
        
        return opportunities  # Return for caching
        
    except Exception as e:
        st.error(f"❌ Error during analysis: {e}")
        return None


def display_results(opportunities, source_market, target_market, market_options):
    """Display analysis results."""
    
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
        
        with st.expander(f"**[{row['Score']:.0f}]** {product_name}...", expanded=(idx == 0)):
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
                st.link_button("🔗 View on Amazon", product_url)
    
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

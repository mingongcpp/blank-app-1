import streamlit as st
import streamlit.components.v1 as components

GA_ID = "G-XXXXXXXX"  # 👈 换成你自己的

components.html(f"""
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_ID}', {{
    page_title: document.title,
    page_location: window.location.href,
    page_path: window.location.pathname
  }});
</script>
""", height=0)


import streamlit as st
import pandas as pd
import re
from collections import defaultdict
import io

# Set page config
st.set_page_config(
    page_title="Marketing Tactic Classifier",
    page_icon="📊",
    layout="wide"
)

# Initialize session state for dictionaries
if 'dictionaries' not in st.session_state:
    st.session_state.dictionaries = {
        'urgency_marketing': {
            'limited', 'limited time', 'limited run', 'limited edition', 'order now',
            'last chance', 'hurry', 'while supplies last', 'before they\'re gone',
            'selling out', 'selling fast', 'act now', 'don\'t wait', 'today only',
            'expires soon', 'final hours', 'almost gone'
        },
        'exclusive_marketing': {
            'exclusive', 'exclusively', 'exclusive offer', 'exclusive deal',
            'members only', 'vip', 'special access', 'invitation only',
            'premium', 'privileged', 'limited access', 'select customers',
            'insider', 'private sale', 'early access'
        }
    }

def classify_statement(text, dictionaries):
    """Classify a statement based on marketing tactic dictionaries."""
    if pd.isna(text):
        return {}
    
    text_lower = text.lower()
    results = {}
    
    for tactic, keywords in dictionaries.items():
        matches = []
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matches.append(keyword)
        
        results[tactic] = {
            'present': len(matches) > 0,
            'count': len(matches),
            'matches': matches
        }
    
    return results

def process_dataframe(df, dictionaries, text_column):
    """Process the dataframe with classification."""
    # Apply classification
    df['classification'] = df[text_column].apply(lambda x: classify_statement(x, dictionaries))
    
    # Extract results to separate columns
    for tactic in dictionaries.keys():
        df[f'{tactic}_present'] = df['classification'].apply(lambda x: x.get(tactic, {}).get('present', False))
        df[f'{tactic}_count'] = df['classification'].apply(lambda x: x.get(tactic, {}).get('count', 0))
        df[f'{tactic}_matches'] = df['classification'].apply(lambda x: ', '.join(x.get(tactic, {}).get('matches', [])))
    
    return df

# App title and description
st.title("📊 Marketing Tactic Classifier")
st.markdown("""
This app classifies text statements based on marketing tactics using customizable keyword dictionaries.
Upload your CSV file and customize the dictionaries to get started.
""")

# Sidebar for dictionary management
with st.sidebar:
    st.header("📚 Dictionary Management")
    
    # Add new tactic
    with st.expander("➕ Add New Tactic", expanded=False):
        new_tactic_name = st.text_input("Tactic Name", key="new_tactic")
        new_keywords = st.text_area("Keywords (one per line)", key="new_keywords")
        if st.button("Add Tactic"):
            if new_tactic_name and new_keywords:
                keywords_set = {kw.strip() for kw in new_keywords.split('\n') if kw.strip()}
                st.session_state.dictionaries[new_tactic_name] = keywords_set
                st.success(f"Added tactic: {new_tactic_name}")
                st.rerun()
    
    # Edit existing tactics
    st.subheader("Edit Existing Tactics")
    
    for tactic_name in list(st.session_state.dictionaries.keys()):
        with st.expander(f"📝 {tactic_name}", expanded=False):
            # Show current keywords
            current_keywords = '\n'.join(sorted(st.session_state.dictionaries[tactic_name]))
            
            # Edit keywords
            edited_keywords = st.text_area(
                "Keywords (one per line)",
                value=current_keywords,
                key=f"edit_{tactic_name}",
                height=200
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save", key=f"save_{tactic_name}"):
                    keywords_set = {kw.strip() for kw in edited_keywords.split('\n') if kw.strip()}
                    st.session_state.dictionaries[tactic_name] = keywords_set
                    st.success("Saved!")
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{tactic_name}"):
                    del st.session_state.dictionaries[tactic_name]
                    st.success("Deleted!")
                    st.rerun()
    
    # Reset to defaults
    st.divider()
    if st.button("🔄 Reset to Default Dictionaries"):
        st.session_state.dictionaries = {
            'urgency_marketing': {
                'limited', 'limited time', 'limited run', 'limited edition', 'order now',
                'last chance', 'hurry', 'while supplies last', 'before they\'re gone',
                'selling out', 'selling fast', 'act now', 'don\'t wait', 'today only',
                'expires soon', 'final hours', 'almost gone'
            },
            'exclusive_marketing': {
                'exclusive', 'exclusively', 'exclusive offer', 'exclusive deal',
                'members only', 'vip', 'special access', 'invitation only',
                'premium', 'privileged', 'limited access', 'select customers',
                'insider', 'private sale', 'early access'
            }
        }
        st.success("Reset to defaults!")
        st.rerun()

# Main content area
tab1, tab2, tab3 = st.tabs(["📤 Upload & Process", "📊 Results", "📈 Statistics"])

with tab1:
    st.header("Upload Your Data")
    
    # File upload
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
    
    if uploaded_file is not None:
        # Read the file
        df = pd.read_csv(uploaded_file)
        
        st.success(f"✅ File uploaded successfully! ({len(df)} rows)")
        
        # Show preview
        st.subheader("Data Preview")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Select text column
        st.subheader("Select Text Column")
        text_column = st.selectbox(
            "Which column contains the text to classify?",
            options=df.columns.tolist(),
            index=0 if 'Statement' not in df.columns else df.columns.tolist().index('Statement')
        )
        
        # Process button
        if st.button("🚀 Classify Statements", type="primary"):
            with st.spinner("Processing..."):
                # Process the dataframe
                processed_df = process_dataframe(df.copy(), st.session_state.dictionaries, text_column)
                
                # Store in session state
                st.session_state.processed_df = processed_df
                st.session_state.text_column = text_column
                
                st.success("✅ Classification complete!")
                st.balloons()

with tab2:
    st.header("Classification Results")
    
    if 'processed_df' in st.session_state:
        df_result = st.session_state.processed_df
        text_col = st.session_state.text_column
        
        # Display options
        col1, col2 = st.columns([3, 1])
        with col1:
            filter_option = st.selectbox(
                "Filter results",
                ["Show All", "Show Only Matches", "Show Only Non-Matches"]
            )
        
        # Filter data based on selection
        if filter_option == "Show Only Matches":
            present_cols = [f'{t}_present' for t in st.session_state.dictionaries.keys()]
            df_display = df_result[df_result[present_cols].any(axis=1)]
        elif filter_option == "Show Only Non-Matches":
            present_cols = [f'{t}_present' for t in st.session_state.dictionaries.keys()]
            df_display = df_result[~df_result[present_cols].any(axis=1)]
        else:
            df_display = df_result
        
        st.info(f"Showing {len(df_display)} of {len(df_result)} statements")
        
        # Show detailed results
        for idx, row in df_display.iterrows():
            with st.expander(f"Row {idx + 1}: {str(row[text_col])[:100]}..."):
                st.markdown(f"**Full Text:** {row[text_col]}")
                st.divider()
                
                # Show classification results
                for tactic in st.session_state.dictionaries.keys():
                    if row[f'{tactic}_present']:
                        st.markdown(f"✅ **{tactic}**: {row[f'{tactic}_matches']}")
                    else:
                        st.markdown(f"❌ **{tactic}**: No matches")
        
        # Download results
        st.divider()
        st.subheader("Download Results")
        
        # Create download button
        csv = df_result.to_csv(index=False)
        st.download_button(
            label="📥 Download Classified Data (CSV)",
            data=csv,
            file_name="classified_data.csv",
            mime="text/csv",
            type="primary"
        )
        
    else:
        st.info("👆 Please upload and process a file in the 'Upload & Process' tab first.")

with tab3:
    st.header("Statistics & Summary")
    
    if 'processed_df' in st.session_state:
        df_stats = st.session_state.processed_df
        
        # Overall stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Statements", len(df_stats))
        
        with col2:
            present_cols = [f'{t}_present' for t in st.session_state.dictionaries.keys()]
            statements_with_tactics = (df_stats[present_cols].any(axis=1)).sum()
            st.metric("Statements with Any Tactic", statements_with_tactics)
        
        with col3:
            percentage = (statements_with_tactics / len(df_stats) * 100) if len(df_stats) > 0 else 0
            st.metric("Coverage", f"{percentage:.1f}%")
        
        st.divider()
        
        # Per-tactic statistics
        st.subheader("Tactic Breakdown")
        
        stats_data = []
        for tactic in st.session_state.dictionaries.keys():
            total_present = df_stats[f'{tactic}_present'].sum()
            percentage = (total_present / len(df_stats) * 100) if len(df_stats) > 0 else 0
            total_matches = df_stats[f'{tactic}_count'].sum()
            
            stats_data.append({
                'Tactic': tactic,
                'Statements': total_present,
                'Percentage': f"{percentage:.1f}%",
                'Total Matches': total_matches
            })
        
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        # Visualization
        st.subheader("Visual Distribution")
        st.bar_chart(stats_df.set_index('Tactic')['Statements'])
        
    else:
        st.info("👆 Please upload and process a file in the 'Upload & Process' tab first.")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    <small>Marketing Tactic Classifier | Built with Streamlit</small>
</div>
""", unsafe_allow_html=True)

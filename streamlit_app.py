import streamlit as st
import pandas as pd
import re
import json

# Set page config
st.set_page_config(
    page_title="Text Classification Tool",
    page_icon="📝",
    layout="wide"
)

# Initialize session state for dictionaries
if 'dictionaries' not in st.session_state:
    st.session_state.dictionaries = {
        'promotional': ['sale', 'discount', 'offer', 'deal', 'limited', 'order', 'buy'],
        'descriptive': ['perfect', 'classic', 'gorgeous', 'excellence', 'quality'],
        'personal': ['my', 'me', 'i', 'smile', 'goal', 'today'],
        'action': ['get', 'order', 'contact', 'touch', 'reach']
    }

def classify_text(text, dictionaries):
    """Classify text based on dictionary keywords."""
    if pd.isna(text):
        return {}
    
    text_lower = text.lower()
    results = {}
    
    for category, keywords in dictionaries.items():
        matches = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_lower)]
        if matches:
            results[category] = matches
    
    return results

def main():
    st.title("📝 Text Classification Tool")
    st.markdown("Upload your CSV file and customize classification dictionaries to categorize text data.")
    
    # Sidebar for dictionary management
    with st.sidebar:
        st.header("⚙️ Dictionary Settings")
        
        # Option to reset to defaults
        if st.button("Reset to Defaults"):
            st.session_state.dictionaries = {
                'promotional': ['sale', 'discount', 'offer', 'deal', 'limited', 'order', 'buy'],
                'descriptive': ['perfect', 'classic', 'gorgeous', 'excellence', 'quality'],
                'personal': ['my', 'me', 'i', 'smile', 'goal', 'today'],
                'action': ['get', 'order', 'contact', 'touch', 'reach']
            }
            st.rerun()
        
        st.markdown("---")
        
        # Edit existing categories
        st.subheader("Edit Categories")
        categories_to_delete = []
        
        for category in list(st.session_state.dictionaries.keys()):
            with st.expander(f"📁 {category.title()}", expanded=False):
                # Display current keywords
                keywords_text = ", ".join(st.session_state.dictionaries[category])
                new_keywords = st.text_area(
                    "Keywords (comma-separated)",
                    value=keywords_text,
                    key=f"edit_{category}",
                    height=100
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update", key=f"update_{category}"):
                        # Parse and update keywords
                        updated_keywords = [kw.strip() for kw in new_keywords.split(',') if kw.strip()]
                        st.session_state.dictionaries[category] = updated_keywords
                        st.success(f"Updated {category}!")
                        st.rerun()
                
                with col2:
                    if st.button("Delete", key=f"delete_{category}"):
                        categories_to_delete.append(category)
        
        # Delete marked categories
        for cat in categories_to_delete:
            del st.session_state.dictionaries[cat]
            st.rerun()
        
        st.markdown("---")
        
        # Add new category
        st.subheader("Add New Category")
        new_category_name = st.text_input("Category Name")
        new_category_keywords = st.text_area("Keywords (comma-separated)")
        
        if st.button("Add Category"):
            if new_category_name and new_category_keywords:
                keywords = [kw.strip() for kw in new_category_keywords.split(',') if kw.strip()]
                st.session_state.dictionaries[new_category_name.lower()] = keywords
                st.success(f"Added category: {new_category_name}")
                st.rerun()
            else:
                st.error("Please provide both category name and keywords")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📤 Upload Data")
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="Upload a CSV file with a column containing text to classify"
        )
    
    with col2:
        st.header("📊 Current Dictionary")
        st.json(st.session_state.dictionaries)
    
    if uploaded_file is not None:
        try:
            # Read the uploaded file
            df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ File uploaded successfully! Found {len(df)} rows.")
            
            # Select the text column to classify
            st.subheader("Select Text Column")
            text_columns = df.columns.tolist()
            selected_column = st.selectbox(
                "Choose the column containing text to classify:",
                text_columns
            )
            
            if st.button("🚀 Classify Text", type="primary"):
                with st.spinner("Classifying text..."):
                    # Apply classification
                    df['classification'] = df[selected_column].apply(
                        lambda x: classify_text(x, st.session_state.dictionaries)
                    )
                    df['categories'] = df['classification'].apply(
                        lambda x: list(x.keys()) if x else []
                    )
                    df['matched_keywords'] = df['classification'].apply(
                        lambda x: {k: v for k, v in x.items()} if x else {}
                    )
                
                st.success("✅ Classification complete!")
                
                # Display results
                st.subheader("Classification Results")
                
                # Summary statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Rows", len(df))
                with col2:
                    classified_count = df['categories'].apply(len).sum()
                    st.metric("Total Classifications", classified_count)
                with col3:
                    rows_with_matches = (df['categories'].apply(len) > 0).sum()
                    st.metric("Rows with Matches", rows_with_matches)
                
                # Category distribution
                st.subheader("📊 Category Distribution")
                category_counts = {}
                for categories in df['categories']:
                    for cat in categories:
                        category_counts[cat] = category_counts.get(cat, 0) + 1
                
                if category_counts:
                    category_df = pd.DataFrame(
                        list(category_counts.items()),
                        columns=['Category', 'Count']
                    ).sort_values('Count', ascending=False)
                    st.bar_chart(category_df.set_index('Category'))
                else:
                    st.info("No matches found in the dataset.")
                
                # Display detailed results
                st.subheader("Detailed Results")
                
                # Filter options
                filter_col1, filter_col2 = st.columns(2)
                with filter_col1:
                    show_only_matches = st.checkbox("Show only rows with matches", value=False)
                with filter_col2:
                    category_filter = st.multiselect(
                        "Filter by category:",
                        options=list(st.session_state.dictionaries.keys())
                    )
                
                # Apply filters
                display_df = df.copy()
                if show_only_matches:
                    display_df = display_df[display_df['categories'].apply(len) > 0]
                
                if category_filter:
                    display_df = display_df[
                        display_df['categories'].apply(
                            lambda x: any(cat in x for cat in category_filter)
                        )
                    ]
                
                # Show results table
                st.dataframe(
                    display_df[[selected_column, 'categories', 'matched_keywords']],
                    use_container_width=True,
                    height=400
                )
                
                # Download results
                st.subheader("💾 Download Results")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # CSV download
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="classified_data.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # JSON download (for matched keywords)
                    json_data = df.to_json(orient='records', indent=2)
                    st.download_button(
                        label="📥 Download as JSON",
                        data=json_data,
                        file_name="classified_data.json",
                        mime="application/json"
                    )
        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("Please ensure your CSV file is properly formatted.")
    
    else:
        st.info("👆 Please upload a CSV file to get started.")
        
        # Show example format
        with st.expander("📋 Example CSV Format"):
            example_df = pd.DataFrame({
                'ID': [1, 2, 3],
                'Statement': [
                    'Get this amazing discount offer today!',
                    'This is a perfect and classic design',
                    'Contact me to reach your goals'
                ]
            })
            st.dataframe(example_df)
            st.caption("Your CSV should have at least one column with text to classify.")

if __name__ == "__main__":
    main()

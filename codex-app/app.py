import streamlit as st
import pandas as pd

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["Classification", "Settings"])

# Classification dictionary
categories = {
    'product_features': ['perfect', 'classic', 'excellence', 'gorgeous'],
    'call_to_action': ['get in touch', 'order'],
    'personal': ['my goal', 'smile', 'someone']
}

def classify_statement(text):
    text_lower = text.lower()
    matches = []
    for category, keywords in categories.items():
        if any(keyword in text_lower for keyword in keywords):
            matches.append(category)
    return matches if matches else ['uncategorized']

if page == "Classification":
    st.title("Dictionary Classification")

    uploaded_file = st.file_uploader("Upload CSV", type=['csv'])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        df['Category'] = df['Statement'].apply(classify_statement)

        st.dataframe(df[['Statement', 'Category']])

        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Results",
            data=csv,
            file_name="classified_data.csv",
            mime="text/csv"
        )

elif page == "Settings":
    st.title("Settings")
    st.write("Configure your classification categories here.")

    for category, keywords in categories.items():
        st.subheader(category)
        st.write(", ".join(keywords))

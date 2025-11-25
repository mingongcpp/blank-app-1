"""Streamlit page that replicates the dictionary classification script."""
import json
from io import StringIO

import numpy as np
import pandas as pd
import streamlit as st

# ========== 1. Defaults copied from the original script ==========
TEXT_COL = "Statement"

TACTIC_DICTIONARY = {
    "scarcity": [
        "last chance",
        "last week",
        "limited time",
        "only a few",
        "before they're gone",
        "while stocks last",
    ],
    "urgency": [
        "today only",
        "now",
        "hurry",
        "right away",
        "don't wait",
        "immediately",
    ],
    "social_proof": [
        "popular",
        "bestseller",
        "customers love",
        "everyone",
        "most people",
        "thousands of",
    ],
    "discount": [
        "discount",
        "sale",
        "off",
        "% off",
        "save",
        "special offer",
        "deal",
    ],
}


# ========== 2. Classification helper ==========
def classify_statement(text, dictionary, return_multiple=False):
    if not isinstance(text, str):
        return np.nan

    text_lower = text.lower()
    matched_labels = []

    for label, keywords in dictionary.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                matched_labels.append(label)
                break

    if not matched_labels:
        return np.nan

    if return_multiple:
        return ";".join(matched_labels)

    return matched_labels[0]


def parse_dictionary(raw_text):
    try:
        parsed = json.loads(raw_text)
        if not isinstance(parsed, dict):
            raise ValueError("Dictionary must be a JSON object where keys map to keyword lists.")

        for label, items in parsed.items():
            if not isinstance(label, str):
                raise ValueError("Each label must be a string.")
            if not isinstance(items, list):
                raise ValueError(f"Keywords for '{label}' must be a list of strings.")
            for value in items:
                if not isinstance(value, str):
                    raise ValueError(f"Keyword '{value}' in label '{label}' must be a string.")

        return parsed, None
    except Exception as exc:  # noqa: BLE001
        return TACTIC_DICTIONARY, str(exc)


# ========== 3. Streamlit page ==========
def main():
    st.set_page_config(page_title="Codex Dictionary Classifier", page_icon="🧠", layout="wide")

    st.title("🧠 Codex Dictionary Classifier")
    st.write(
        "Upload a CSV, pick the text column, optionally edit the keyword dictionary, "
        "and the app will generate the same single and multi-label outputs produced by the original script."
    )

    with st.sidebar:
        st.header("Keyword dictionary")
        dict_json = json.dumps(TACTIC_DICTIONARY, indent=2)
        dict_input = st.text_area("JSON dictionary", value=dict_json, height=260)
        user_dictionary, dict_error = parse_dictionary(dict_input)
        if dict_error:
            st.error(f"Dictionary error: {dict_error}. Using defaults.")
        else:
            st.success("Dictionary loaded ✅")

    st.header("1. Upload your CSV")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    df = None
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.write("Preview of your data:")
            st.dataframe(df.head())
        except Exception as exc:  # noqa: BLE001
            st.error(f"Unable to read CSV: {exc}")

    if df is None:
        st.info("Upload a CSV that contains a 'Statement' column to begin.")
        return

    st.header("2. Choose the text column")
    columns = list(df.columns)
    default_index = columns.index(TEXT_COL) if TEXT_COL in columns else 0
    text_col = st.selectbox("Select the column to classify", options=columns, index=default_index)

    st.header("3. Run classification")
    if st.button("Classify statements", type="primary"):
        with st.spinner("Running dictionary match..."):
            df["Tactic_dict_single"] = df[text_col].apply(
                lambda x: classify_statement(x, user_dictionary, return_multiple=False)
            )
            df["Tactic_dict_multi"] = df[text_col].apply(
                lambda x: classify_statement(x, user_dictionary, return_multiple=True)
            )

        st.success("Classification complete!")
        st.dataframe(df[[text_col, "Tactic_dict_single", "Tactic_dict_multi"]].head(20))

        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download results as CSV",
            data=csv_buffer.getvalue().encode("utf-8"),
            file_name="sample_data_with_dict_labels.csv",
            mime="text/csv",
        )

        st.subheader("Dictionary used in this run")
        st.json(user_dictionary)


if __name__ == "__main__":
    main()

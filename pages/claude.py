import json
import io

import numpy as np
import pandas as pd
import streamlit as st

# ========== 1. Default settings ==========

# Default name of the text column to classify.
DEFAULT_TEXT_COL = "Statement"

# Default dictionary of tactics -> keywords.
DEFAULT_TACTIC_DICTIONARY = {
    "scarcity": [
        "last chance", "last week", "limited time", "only a few",
        "before they’re gone", "while stocks last"
    ],
    "urgency": [
        "today only", "now", "hurry", "right away",
        "don’t wait", "immediately"
    ],
    "social_proof": [
        "popular", "bestseller", "customers love", "everyone",
        "most people", "thousands of"
    ],
    "discount": [
        "discount", "sale", "off", "% off", "save",
        "special offer", "deal"
    ],
    # You can add more labels here.
}


# ========== 2. Classifier function ==========

def classify_statement(text, dictionary, return_multiple=False):
    """
    text: string to classify
    dictionary: dict[label] -> list of keywords
    return_multiple: if True, return all matching labels as list.
                     if False, return the first match based on dict order.
    """
    if not isinstance(text, str):
        return np.nan

    text_lower = text.lower()
    matched_labels = []

    # Loop in dictionary order -> can be used as priority order
    for label, keywords in dictionary.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                matched_labels.append(label)
                break  # stop after first keyword match for this label

    if not matched_labels:
        return np.nan

    if return_multiple:
        return ";".join(matched_labels)  # or return matched_labels as a list

    # Single-label: use first matched label (priority by dict order)
    return matched_labels[0]


# ========== 3. Streamlit app ==========

def main():
    st.set_page_config(page_title="Tactic Dictionary Classifier", layout="wide")

    st.title("🔍 Tactic Dictionary Text Classifier")
    st.write(
        "Upload a CSV file, choose the text column, edit the tactic–keyword "
        "dictionary, and classify each row using simple keyword matching."
    )

    # ---------- 3.1 File upload ----------
    st.header("1. Upload your dataset")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            return

        st.success("File uploaded successfully!")
        st.write("Preview of your data:")
        st.dataframe(df.head())
    else:
        st.info("👆 Upload a CSV file to get started.")
        df = None

    # ---------- 3.2 Choose text column ----------
    text_col = DEFAULT_TEXT_COL
    if df is not None:
        st.header("2. Choose the text column")
        cols = list(df.columns)

        if DEFAULT_TEXT_COL in cols:
            default_index = cols.index(DEFAULT_TEXT_COL)
        else:
            default_index = 0

        text_col = st.selectbox(
            "Select the column that contains the text to classify:",
            options=cols,
            index=default_index,
        )

    # ---------- 3.3 Dictionary editor ----------
    st.header("3. Edit the tactic dictionary")

    st.markdown(
        "The dictionary is a JSON object where:\n\n"
        "- **Keys** are tactic/label names (strings)\n"
        "- **Values** are lists of keywords/phrases (strings)\n\n"
        "You can edit the JSON below to add/remove tactics or keywords."
    )

    default_dict_str = json.dumps(DEFAULT_TACTIC_DICTIONARY, indent=2, ensure_ascii=False)
    dict_text = st.text_area(
        "Tactic dictionary (JSON format)",
        value=default_dict_str,
        height=250,
    )

    # Try to parse user-edited dictionary
    user_dictionary = DEFAULT_TACTIC_DICTIONARY
    dict_valid = True
    error_msg = ""

    try:
        parsed = json.loads(dict_text)

        # Basic validation: must be dict[str, list[str]]
        if not isinstance(parsed, dict):
            raise ValueError("The root JSON object must be a dictionary.")

        for k, v in parsed.items():
            if not isinstance(k, str):
                raise ValueError("All keys must be strings.")
            if not isinstance(v, list):
                raise ValueError(f"Value for key '{k}' must be a list.")
            for item in v:
                if not isinstance(item, str):
                    raise ValueError(
                        f"All items in list for key '{k}' must be strings."
                    )

        user_dictionary = parsed

    except Exception as e:
        dict_valid = False
        error_msg = str(e)

    if dict_valid:
        st.success("Dictionary parsed successfully ✅")
    else:
        st.error(
            "There is an error in the dictionary JSON. "
            f"The default dictionary will be used instead.\n\nError: {error_msg}"
        )

    # ---------- 3.4 Classification options ----------
    st.header("4. Classification options")

    col1, col2 = st.columns(2)

    with col1:
        return_multiple = st.checkbox(
            "Return multiple labels (semicolon-separated)",
            value=True,
            help="If checked, all matching tactics are returned as a semicolon-separated string.",
        )

    with col2:
        single_col_name = st.text_input(
            "Name of single-label column",
            value="Tactic_dict_single",
        )

    multi_col_name = st.text_input(
        "Name of multi-label column",
        value="Tactic_dict_multi",
    )

    # ---------- 3.5 Run classification ----------
    st.header("5. Run classification")

    run = st.button("Classify text")

    if run:
        if df is None:
            st.error("Please upload a CSV file first.")
            return

        if text_col not in df.columns:
            st.error(f"Selected text column '{text_col}' not found in dataframe.")
            return

        # Use either the user-edited dictionary (if valid) or the default
        dictionary_to_use = user_dictionary if dict_valid else DEFAULT_TACTIC_DICTIONARY

        with st.spinner("Classifying statements..."):
            # Single label column
            df[single_col_name] = df[text_col].apply(
                lambda x: classify_statement(
                    x, dictionary_to_use, return_multiple=False
                )
            )

            # Multi-label column (if requested)
            if return_multiple:
                df[multi_col_name] = df[text_col].apply(
                    lambda x: classify_statement(
                        x, dictionary_to_use, return_multiple=True
                    )
                )

        st.success("Classification complete! 🎉")

        st.subheader("Preview of results")
        preview_cols = [text_col, single_col_name]
        if return_multiple:
            preview_cols.append(multi_col_name)

        st.dataframe(df[preview_cols].head(20))

        # ---------- 3.6 Download results ----------
        st.subheader("Download results")
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue().encode("utf-8")

        st.download_button(
            label="📥 Download CSV with labels",
            data=csv_data,
            file_name="sample_data_with_dict_labels_streamlit.csv",
            mime="text/csv",
        )

        st.markdown("Dictionary used for this run:")
        st.json(dictionary_to_use)


if __name__ == "__main__":
    main()


import os
from pathlib import Path
import pandas as pd
import streamlit as st
from extract_text import extract_text_from_file
from embed_store import create_faiss_index
from rag_swot import generate_swot
from utils import generate_summary, generate_swot_pdf
from financials import get_cik, fetch_financials
from main_refactored import run_pipeline

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Title
st.set_page_config(page_title="Competitor Intelligence App", layout="wide")
st.title("Competitor Intelligence Suite")
#file_type = st.selectbox("Choose analysis type", ["SWOT", "Financial Metrics"])

# Sidebar selector
module = st.sidebar.radio("Choose an analysis module:", ["SWOT Generator", "Financial Metrics"])

if module == "SWOT Generator":
    st.header("SWOT Analysis from Transcript")
    uploaded_file = st.file_uploader("Upload transcript (.pdf or .txt)", type=["pdf", "txt"])

    if uploaded_file:
        # Check if cached SWOT exists and file is same
        if 'swot_result' not in st.session_state or st.session_state.get('last_uploaded_file') != uploaded_file.name:
            with st.spinner("Extracting and analyzing SWOT..."):
                ext = Path(uploaded_file.name).suffix.lower()
                # Extract text for any file type since function handles both
                text = extract_text_from_file(uploaded_file)
                vectorstore, _ = create_faiss_index(text)
                swot = generate_swot(vectorstore)
                summary = generate_summary(swot)
                pdf_bytes = generate_swot_pdf(swot, company_name=uploaded_file.name)

                # Save results in session state
                st.session_state['swot_result'] = swot
                st.session_state['swot_summary'] = summary
                st.session_state['swot_pdf_bytes'] = pdf_bytes
                st.session_state['last_uploaded_file'] = uploaded_file.name
        else:
            # Load cached results
            swot = st.session_state['swot_result']
            summary = st.session_state['swot_summary']
            pdf_bytes = st.session_state['swot_pdf_bytes']

        st.success("SWOT Analysis Complete!")
        st.subheader("Summary")
        st.markdown(summary)

        st.subheader("Download SWOT Report")
        st.download_button(
            label="Download SWOT as PDF",
            data=pdf_bytes,
            file_name=f"{uploaded_file.name.split('.')[0]}_swot.pdf",
            mime="application/pdf"
        )

# Financial Metrics Block
elif module == "Financial Metrics":
    st.header("Financial Report Analyzer")
    
    uploaded_financial_file = st.file_uploader("Upload Financial Report (PDF or TXT)", type=["pdf", "txt"])
    
    if uploaded_financial_file:
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / uploaded_financial_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_financial_file.read())
        st.success(f"Uploaded file saved to {file_path}")

    ticker = st.text_input("Enter Stock Ticker (e.g., UNH)")
    email = st.text_input("Enter your email (for SEC API)", value="you@example.com")
    start = st.date_input("Start Date", value=pd.to_datetime("2021-01-01"))
    end = st.date_input("End Date", value=pd.to_datetime("2024-12-31"))

    if st.button("Run Financial Metrics") and ticker and email:
        try:
            with st.spinner("Running financial data pipeline..."):
                outputs = run_pipeline(ticker, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), email)
            st.success("Financial metrics generated successfully!")

            # Cache the dataframes in session_state
            st.session_state['financial_outputs'] = {}
            for key, path_str in outputs.items():
                csv_path = Path(path_str)
                if csv_path.exists():
                    df = pd.read_csv(csv_path)
                    st.session_state['financial_outputs'][key] = df

        except Exception as e:
            st.error(f"Error running financial pipeline: {e}")

# Outside the above block, add this to show cached tables and download buttons:

#if 'financial_outputs' in st.session_state:
 #   for key, df in st.session_state['financial_outputs'].items():
  #      st.subheader(f"{key.replace('_', ' ').title()} Data")
   #     st.dataframe(df)
    #    csv_bytes = df.to_csv(index=False).encode("utf-8")
     #   st.download_button(
      #      label=f"Download {key}.csv",
       #     data=csv_bytes,
        #    file_name=f"{key}.csv",
         #   mime="text/csv"
        #)

if 'financial_outputs' in st.session_state:
    for key, df in st.session_state['financial_outputs'].items():
        st.subheader(f"{key.replace('_', ' ').title()} Data")
        st.dataframe(df)
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"Download {key}.csv",
            data=csv_bytes,
            file_name=f"{key}.csv",
            mime="text/csv"
        )

    # 📊 Plot stock price trend from merged data
    if 'merged' in st.session_state["financial_outputs"]:
        df_merged = st.session_state["financial_outputs"]["merged"]
        ticker_col = f"{ticker.upper()}_Close"

        if ticker_col in df_merged.columns:
            # Ensure datetime index
            if not pd.api.types.is_datetime64_any_dtype(df_merged.index):
                if "end" in df_merged.columns:
                    df_merged["end"] = pd.to_datetime(df_merged["end"], errors='coerce')
                    df_merged.set_index("end", inplace=True)

            if "Return" not in df_merged.columns:
                df_merged["Return"] = df_merged[ticker_col].pct_change()
                st.session_state["financial_outputs"]["merged"] = df_merged

            if ticker_col in df_merged.columns and "Return" in df_merged.columns:
                import matplotlib.pyplot as plt
                st.subheader("📈 Stock Price Trend")
                y = df_merged[ticker_col].dropna()
                fig, ax = plt.subplots()
                ax.plot(y.index, y, label=ticker_col, marker='o')
                ax.set_ylabel("Price")
                ax.set_xlabel("Date")
                ax.set_title(f"{ticker.upper()} Stock Price Over Time")
                ax.legend()
                st.pyplot(fig)
            else:
                st.warning(f"'{ticker_col}' or 'Return' column missing. Columns: {list(df_merged.columns)}")
        else:
            st.warning(f"'{ticker_col}' not found in merged data columns: {list(df_merged.columns)}")
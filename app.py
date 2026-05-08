import streamlit as st
import pandas as pd
from groq import Groq
from fpdf import FPDF
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("Groq_API_KEY"))

st.title("AI Business Analyst")
st.write("Upload your sales data and get instant insights")
st.divider()

uploaded_file = st.file_uploader("Choose file", type=["csv", "xlsx", "xls"])

@st.cache_data
def load_file(file):
    if file.name.endswith("csv"):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)
    
def generate_pdf(report_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "AI Business Report", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", size=11)
    clean_text = report_text.replace("**", "").replace("$", "USD ")
    for line in clean_text.split("\n"):
        if line.strip():
            pdf.multi_cell(0, 8, line)
            pdf.ln(2)
    return pdf.output()

if uploaded_file is not None:
    df = load_file(uploaded_file)

    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    all_columns = df.columns.tolist()

    st.write("Uploaded Data:")
    st.dataframe(df)
    st.divider()
    st.header("Configure your Analysis")

    analysis_mode = st.radio(
        "How do you want to Analyze?",
        ["Full Auto Analysis", "Custom Analysis"],
        index=0
    )

    if analysis_mode == "Full Auto Analysis":
        if st.button("Analyze My Data"):
            st.subheader("Data Overview")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", df.shape[0])
            with col2:
                st.metric("Total Columns", df.shape[1])
            with col3:
                st.metric("Missing Values", df.isnull().sum().sum())

            st.subheader("Summary Statistics")
            st.dataframe(df.describe())

            st.subheader("Distribution of Numeric Columns")
            for col in numeric_columns:
                st.write(f"**{col}**")
                st.bar_chart(df[col].describe())

            st.divider()
            st.subheader("AI Business Report")
            summary = f"""
            Dataset has {df.shape[0]} rows and {df.shape[1]} columns.
            Numeric columns: {numeric_columns}
            Basic statistics: {df.describe().to_string()}
            """
            with st.spinner("Generating AI report..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                 messages=[{"role": "user","content":f"""
                You are a senior business consultant. Analyze this data and write a concise professional business report.
                
                Format it exactly like this:
                **Executive Summary** (2-3 sentences max)
                **Key Findings** (3-4 bullet points, specific numbers only)

                **Risk Areas** (2-3 bullet points)

                **Recommendations** (3 actionable recommendations)

                Be concise. Use specific numbers from the data. No generic advice. No filler sentences.
                Data:
                {summary}
                """}]

                )
                st.markdown(response.choices[0].message.content.replace("$", "\\$"))

                pdf_bytes = generate_pdf(response.choices[0].message.content)
                st.download_button(
                     label="Download Report as PDF",
                    data=bytes(pdf_bytes),
                    file_name="business_report.pdf",
                     mime="application/pdf"
                )

    else:
        with st.expander("Configure Custom Analysis", expanded=False):
            value_col = st.selectbox("Select your Main Value Column", numeric_columns)
            category_col = st.selectbox("Select your Category Column", all_columns)
            date_col = st.selectbox("Select your Date Column (optional)", ["None"] + all_columns)
            analyze = st.button("Analyze My Data")

        if analyze:
            df = df.copy()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total", f"{df[value_col].sum():,.2f}")
            with col2:
                st.metric("Average", f"{df[value_col].mean():,.2f}")
            with col3:
                st.metric(f"Top {category_col}", df.groupby(category_col)[value_col].sum().idxmax())

            st.divider()
            st.subheader(f"{value_col} by {category_col}")
            chart_data = df.groupby(category_col)[value_col].sum().sort_values(ascending=False)
            st.bar_chart(chart_data)

            st.subheader(f"Top 10 {category_col} by {value_col}")
            top_10 = df.groupby(category_col)[value_col].sum().sort_values(ascending=False).head(10)
            st.bar_chart(top_10)

            if date_col != "None":
                try:
                    df[date_col] = pd.to_datetime(df[date_col])
                    trend = df.groupby(date_col)[value_col].sum()
                    st.subheader("Trend Over Time")
                    st.line_chart(trend)
                except Exception:
                    st.warning("Selected date column doesn't appear to contain valid dates.")

            st.divider()
            st.subheader("AI Business Report")
            summary = f"""
            Dataset has {df.shape[0]} rows and {df.shape[1]} columns.
            Value column: {value_col}
            Category column: {category_col}
            Total: {df[value_col].sum():,.2f}
            Average: {df[value_col].mean():,.2f}
            Top category: {df.groupby(category_col)[value_col].sum().idxmax()}
            Basic statistics: {df[value_col].describe().to_string()}
            """
            with st.spinner("Generating AI report..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                     messages=[{"role": "user","content":f"""
                You are a senior business consultant. Analyze this data and write a concise professional business report.
                
                Format it exactly like this:
                **Executive Summary** (2-3 sentences max)
                **Key Findings** (3-4 bullet points, specific numbers only)

                **Risk Areas** (2-3 bullet points)

                **Recommendations** (3 actionable recommendations)

                Be concise. Use specific numbers from the data. No generic advice. No filler sentences.
                Data:
                {summary}
                """}]

                )
                st.markdown(response.choices[0].message.content.replace("$", "\\$"))
                pdf_bytes = generate_pdf(response.choices[0].message.content)
                st.download_button(
                        label="Download Report as PDF",
                          data=bytes(pdf_bytes),
                        file_name="business_report.pdf",
                         mime="application/pdf"
                )
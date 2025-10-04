import streamlit as st
import pandas as pd
import os
import json
import requests
from dotenv import load_dotenv
from groq import Groq
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CORESIGNAL_API_KEY = os.getenv("CORESIGNAL_API_KEY")

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)

# Page config
st.set_page_config(page_title="AI Sourcing Agent with Coresignal MCP", layout="wide")

# Backend functions
def parse_query_with_llm(user_query: str):
    if not GROQ_API_KEY:
        return {"type": "unknown", "error": "GROQ API key not configured"}
    
    prompt = f"""
    Decide if this query is about COMPANIES or EMPLOYEES.
    Then convert it into JSON filters (valid JSON only, no code fences).

    Query: "{user_query}"

    Example 1 (company):
    {{
      "type": "company",
      "industry": "Pharma",
      "location": "Bangalore",
      "keywords": ["cloud"],
      "min_employees": 50
    }}

    Example 2 (employee):
    {{
      "type": "employee",
      "company": "Infosys",
      "location": "Bangalore",
      "skills": ["Data Science", "Python"]
    }}
    """
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    parsed_text = response.choices[0].message.content.strip()
    try:
        filters = json.loads(parsed_text)
    except Exception as e:
        filters = {"type": "unknown", "raw_text": parsed_text}
    return filters

def fetch_employees(filters):
    if not CORESIGNAL_API_KEY:
        return []
    
    url = "https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl/preview"
    must_clauses = []
    if "company" in filters:
        must_clauses.append({"match": {"company_name": filters["company"]}})
    if "location" in filters:
        must_clauses.append({"match": {"location_country": filters["location"]}})
    if "skills" in filters:
        for skill in filters["skills"]:
            must_clauses.append({"match": {"skills": skill}})
    payload = {"query": {"bool": {"must": must_clauses}}} if must_clauses else {"query": {"match_all": {}}}
    headers = {"Content-Type": "application/json", "apikey": CORESIGNAL_API_KEY}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        return []
    data = response.json()
    employees_list = data if isinstance(data, list) else data.get("employees", data.get("hits", data.get("results", [])))
    results = []
    for e in employees_list:
        results.append({
            "Name": e.get("full_name", "N/A"),
            "Title": e.get("job_title", "N/A"),
            "Company": e.get("company_name", "N/A"),
            "Location": e.get("location_country", "N/A"),
            "Connections": e.get("connections_count", "N/A")
        })
    return results

def fetch_companies(filters):
    if not CORESIGNAL_API_KEY:
        return []
    
    url = "https://api.coresignal.com/cdapi/v2/company_clean/search/es_dsl/preview"
    must_clauses = []
    if "keywords" in filters:
        must_clauses.append({"query_string": {"query": " ".join(filters["keywords"]), "default_field": "categories_and_keywords","default_operator": "AND"}})
    if "industry" in filters:
        must_clauses.append({"match": {"industry": filters["industry"]}})
    if "location" in filters:
        must_clauses.append({"match": {"location_hq_country": filters["location"]}})
    if "min_employees" in filters:
        must_clauses.append({"range": {"size_range": {"gte": filters["min_employees"]}}})
    payload = {"query": {"bool": {"must": must_clauses}}} if must_clauses else {"query": {"match_all": {}}}
    headers = {"Content-Type": "application/json", "apikey": CORESIGNAL_API_KEY}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        return []
    data = response.json()
    companies_list = data if isinstance(data, list) else data.get("companies", data.get("hits", data.get("results", [])))
    results = []
    for c in companies_list:
        results.append({
            "Name": c.get("name", "N/A"),
            "Industry": c.get("industry", "N/A"),
            "Size": c.get("size_range", "N/A"),
            "Location": c.get("location_hq_country", "N/A"),
            "Website": c.get("websites_main") or c.get("website_main") or c.get("website", "N/A")
        })
    return results

def summarize_results(results, user_query, query_type):
    if not results or not GROQ_API_KEY:
        return "No results found."
    context = "\n".join([f"- {r['Name']} ({r.get('Title', r.get('Industry', ''))} at {r.get('Company', r.get('Location',''))}, {r['Location']})" for r in results])
    prompt = f"""
    User asked: {user_query}
    Here are the {query_type}s found:
    {context}
    Summarize in 3-4 lines and highlight the most relevant ones.
    """
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

# Frontend UI
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

col1, col2 = st.columns([10, 1])
with col1:
    st.title("🌐 AI Sourcing Agent with Coresignal MCP")
with col2:
    if st.button("🌙" if not st.session_state.dark_mode else "☀️", key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

if st.session_state.dark_mode:
    st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; }
    .stApp *, .stMarkdown, .stText, p, h1, h2, h3, label { color: white !important; }
    .stTextInput input { background-color: #262730 !important; color: white !important; border: 1px solid #555 !important; }
    .stSelectbox select, .stMultiSelect div { background-color: #262730 !important; color: white !important; }
    .stButton button, .stDownloadButton button { background-color: #262730 !important; color: white !important; border: 1px solid #555 !important; }
    [data-testid="stDataFrame"] { background-color: #262730 !important; }
    [data-testid="stDataFrame"] > div { background-color: #262730 !important; }
    [data-testid="stDataFrame"] iframe { background-color: #262730 !important; }
    </style>
    """, unsafe_allow_html=True)

# API Key Configuration
if not GROQ_API_KEY or not CORESIGNAL_API_KEY:
    st.error("⚠️ Please configure your API keys in the Hugging Face Spaces secrets:")
    st.code("GROQ_API_KEY=your_groq_api_key\nCORESIGNAL_API_KEY=your_coresignal_api_key")
    st.stop()

with st.container():
    user_query = st.text_input("Enter your main sourcing query:")
    refinement_query = st.text_input("Refinement query (optional, e.g., 'Europe', 'more than 500 employees')")
    search_button = st.button("Search")

if 'filtered_df' not in st.session_state:
    st.session_state.filtered_df = None
if 'data' not in st.session_state:
    st.session_state.data = None

if search_button:
    st.info("Processing your query...")
    
    main_query = user_query
    if refinement_query:
        main_query += " AND " + refinement_query

    filters = parse_query_with_llm(main_query)
    query_type = filters.get("type")

    results = fetch_companies(filters) if query_type == "company" else fetch_employees(filters)
    summary = summarize_results(results, main_query, query_type)

    st.session_state['data'] = {"query_type": query_type, "results": results, "ai_summary": summary}
    df = pd.DataFrame(results)
    st.session_state['filtered_df'] = df.copy()
    
    if df.empty:
        st.warning("No results found.")
    else:
        st.success(f"📊 Found {len(df)} {query_type}(s)")

if st.session_state['filtered_df'] is not None:
    df = st.session_state['filtered_df']

    st.subheader("🔎 Filters")
    filters_col, results_col = st.columns([1, 3])

    with filters_col:
        filtered_df = df.copy()

        if "Location" in df.columns:
            unique_locations = df["Location"].dropna().unique().tolist()
            selected_locations = st.multiselect(
                "Filter by Location",
                options=["Select All"] + unique_locations,
                default=["Select All"]
            )
            if "Select All" not in selected_locations:
                filtered_df = filtered_df[filtered_df["Location"].isin(selected_locations)]

        if "Size" in df.columns:
            unique_sizes = df["Size"].dropna().unique().tolist()
            selected_sizes = st.multiselect(
                "Filter by Size",
                options=["Select All"] + unique_sizes,
                default=["Select All"]
            )
            if "Select All" not in selected_sizes:
                filtered_df = filtered_df[filtered_df["Size"].isin(selected_sizes)]

        if "Connections" in df.columns:
            unique_connections = sorted(df["Connections"].dropna().unique().tolist())
            selected_connections = st.multiselect(
                "Filter by Connections",
                options=["Select All"] + unique_connections,
                default=["Select All"]
            )
            if "Select All" not in selected_connections:
                filtered_df = filtered_df[filtered_df["Connections"].isin(selected_connections)]

        st.session_state['filtered_df'] = filtered_df

    with results_col:
        st.subheader("📋 Filtered Results (Multi-level Highlight)")

        display_df = filtered_df.copy()
        top_n_highlight = 5
        if st.session_state['data']['query_type'] == "employee" and "Connections" in display_df.columns:
            display_df = display_df.sort_values(by="Connections", ascending=False).reset_index(drop=True)
        elif st.session_state['data']['query_type'] == "company" and "Size" in display_df.columns:
            display_df["Size_numeric"] = display_df["Size"].str.extract("(\d+)").astype(float).fillna(0)
            display_df = display_df.sort_values(by="Size_numeric", ascending=False).reset_index(drop=True)
            display_df.drop("Size_numeric", axis=1, inplace=True)

        def combined_highlight(row):
            styles = [''] * len(row)
            query_skills = user_query.lower().split()

            for i, col in enumerate(row.index):
                if row.name < top_n_highlight:
                    styles[i] = 'color: #2b7a0b; font-weight: bold'
                    continue
                if st.session_state['data']['query_type'] == "employee" and col == "Name":
                    row_title = str(row.get("Title", "")).lower()
                    matched_skills = [skill for skill in query_skills if skill in row_title]
                    if len(matched_skills) >= 2:
                        styles[i] = 'color: #800080; font-weight: bold'
                    elif len(matched_skills) == 1:
                        styles[i] = 'color: #ff7f0e; font-weight: bold'
                if st.session_state['data']['query_type'] == "employee" and col == "Connections" and row[col] >= 300:
                    styles[i] = 'color: #1f77b4; font-weight: bold'
                if st.session_state['data']['query_type'] == "company" and col == "Size":
                    try:
                        size_num = int(''.join(filter(str.isdigit, str(row[col]))))
                        if size_num >= 500:
                            styles[i] = 'color: #1f77b4; font-weight: bold'
                    except:
                        pass
            return styles

        st.dataframe(display_df.style.apply(combined_highlight, axis=1), use_container_width=True)

        st.subheader("📂 Export Options")
        csv_col, excel_col, pdf_col = st.columns(3)

        csv = display_df.to_csv(index=False).encode('utf-8')
        with csv_col:
            st.download_button(
                "📥 CSV",
                data=csv,
                file_name=f"{st.session_state['data']['query_type']}_results.csv",
                mime="text/csv"
            )

        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            display_df.to_excel(writer, index=False, sheet_name="Results")
        with excel_col:
            st.download_button(
                "📊 Excel",
                data=excel_buffer.getvalue(),
                file_name=f"{st.session_state['data']['query_type']}_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = [Paragraph("AI Sourcing Results", styles['Title'])]
        table_data = [display_df.columns.tolist()] + display_df.values.tolist()
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2b7a0b")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)
        doc.build(elements)
        with pdf_col:
            st.download_button(
                "📄 PDF",
                data=pdf_buffer.getvalue(),
                file_name=f"{st.session_state['data']['query_type']}_results.pdf",
                mime="application/pdf"
            )

        st.subheader("🤖 AI Suggestion")
        st.write(st.session_state['data']['ai_summary'])
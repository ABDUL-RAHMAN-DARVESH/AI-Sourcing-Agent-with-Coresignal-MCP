import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ------------------------
# Page config
# ------------------------
st.set_page_config(page_title="AI Sourcing Agent with Coresignal MCP", layout="wide")

# Theme toggle
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

# ------------------------
# Inputs
# ------------------------

with st.container():
    user_query = st.text_input("Enter your main sourcing query:")
    refinement_query = st.text_input("Refinement query (optional, e.g., 'Europe', 'more than 500 employees')")
    search_button = st.button("Search")

# Initialize session state
if 'filtered_df' not in st.session_state:
    st.session_state.filtered_df = None
if 'data' not in st.session_state:
    st.session_state.data = None

# ------------------------
# Fetch Data
# ------------------------
if search_button:
    st.info("Fetching data from FastAPI...")
    response = requests.post("http://127.0.0.1:8000/sourcing", json={
        "user_query": user_query,
        "refinement_query": refinement_query
    })

    if response.status_code == 200:
        st.session_state['data'] = response.json()
        df = pd.DataFrame(st.session_state['data']['results'])
        st.session_state['filtered_df'] = df.copy()
        if df.empty:
            st.warning("No results found.")
        else:
            st.success(f"📊 Found {len(df)} {st.session_state['data']['query_type']}(s)")
    else:
        st.error("❌ Error fetching data from FastAPI.")

# ------------------------
# Filters & Results
# ------------------------
if st.session_state['filtered_df'] is not None:
    df = st.session_state['filtered_df']

    st.subheader("🔎 Filters")
    filters_col, results_col = st.columns([1, 3])

    with filters_col:
        filtered_df = df.copy()

        # Location Filter
        if "Location" in df.columns:
            unique_locations = df["Location"].dropna().unique().tolist()
            selected_locations = st.multiselect(
                "Filter by Location",
                options=["Select All"] + unique_locations,
                default=["Select All"]
            )
            if "Select All" not in selected_locations:
                filtered_df = filtered_df[filtered_df["Location"].isin(selected_locations)]

        # Size Filter
        if "Size" in df.columns:
            unique_sizes = df["Size"].dropna().unique().tolist()
            selected_sizes = st.multiselect(
                "Filter by Size",
                options=["Select All"] + unique_sizes,
                default=["Select All"]
            )
            if "Select All" not in selected_sizes:
                filtered_df = filtered_df[filtered_df["Size"].isin(selected_sizes)]

        # Connections Filter
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

    # ------------------------
    # Results Display with Multi-level Highlight
    # ------------------------
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

        # Multi-level highlight
        def combined_highlight(row):
            styles = [''] * len(row)
            query_skills = user_query.lower().split()

            for i, col in enumerate(row.index):
                # Top relevance → Green bold
                if row.name < top_n_highlight:
                    styles[i] = 'color: #2b7a0b; font-weight: bold'
                    continue
                # Skill match → Orange/Purple
                if st.session_state['data']['query_type'] == "employee" and col == "Name":
                    row_title = str(row.get("Title", "")).lower()
                    matched_skills = [skill for skill in query_skills if skill in row_title]
                    if len(matched_skills) >= 2:
                        styles[i] = 'color: #800080; font-weight: bold'
                    elif len(matched_skills) == 1:
                        styles[i] = 'color: #ff7f0e; font-weight: bold'
                # Seniority / Connections / Company Size → Blue
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

        # ------------------------
        # Export Options
        # ------------------------
        st.subheader("📂 Export Options")
        csv_col, excel_col, pdf_col = st.columns(3)

        # CSV Export
        csv = display_df.to_csv(index=False).encode('utf-8')
        with csv_col:
            st.download_button(
                "📥 CSV",
                data=csv,
                file_name=f"{st.session_state['data']['query_type']}_results.csv",
                mime="text/csv"
            )

        # Excel Export
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

        # PDF Export
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

        # ------------------------
        # AI Summary (plain text)
        # ------------------------
        st.subheader("🤖 AI Suggestion")
        st.write(st.session_state['data']['ai_summary'])

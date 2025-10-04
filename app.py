import os
import json
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from pydantic import BaseModel
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware

# ------------------------
# Load environment variables
# ------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CORESIGNAL_API_KEY = os.getenv("CORESIGNAL_API_KEY")

client = Groq(api_key=GROQ_API_KEY)
app = FastAPI()

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ------------------------
# Pydantic Model for input
# ------------------------
class QueryRequest(BaseModel):
    user_query: str
    refinement_query: str = ""

# ------------------------
# LLM Parsing & CoreSignal fetching functions
# ------------------------
def parse_query_with_llm(user_query: str):
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
    if not results:
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

# ------------------------
# FastAPI Endpoint
# ------------------------
@app.post("/sourcing")
def sourcing(query: QueryRequest):
    main_query = query.user_query
    refinement_query = query.refinement_query

    combined_query = main_query
    if refinement_query:
        combined_query += " AND " + refinement_query

    filters = parse_query_with_llm(combined_query)
    query_type = filters.get("type")

    results = fetch_companies(filters) if query_type == "company" else fetch_employees(filters)
    summary = summarize_results(results, combined_query, query_type)

    return {"query_type": query_type, "results": results, "ai_summary": summary}

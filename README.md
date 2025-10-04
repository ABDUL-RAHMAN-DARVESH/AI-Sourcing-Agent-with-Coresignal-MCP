# AI-Powered Sourcing Agent

An intelligent sourcing assistant that uses AI to find companies and employees through natural language queries. Built with FastAPI backend and Streamlit frontend, powered by Groq LLM and Coresignal API.

## Features

- 🤖 Natural language query processing with Groq LLM
- 🏢 Company and employee search via Coresignal API
- 🎨 Interactive Streamlit UI with dark/light theme
- 📊 Advanced filtering and multi-level result highlighting
- 📁 Export results to CSV, Excel, and PDF formats
- 🔍 AI-powered result summarization

## Architecture

- **Backend**: FastAPI server (`app.py`) handles AI processing and API calls
- **Frontend**: Streamlit client (`client.py`) provides interactive UI
- **AI Engine**: Groq LLM for query parsing and result analysis
- **Data Source**: Coresignal API for company and employee data

## Setup

### Prerequisites
- Python 3.13+
- Coresignal API key
- Groq API key

### Installation

1. **Clone and navigate to project**:
```bash
cd "AI-Powered Sourcing Agent"
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**:
Create/update `.env` file:
```env
CORESIGNAL_API_KEY=your_coresignal_api_key
GROQ_API_KEY=your_groq_api_key

```

## How to Run

### Method 1: Two Terminal Setup (Recommended)

**Terminal 1 - Start FastAPI Backend**:
```bash
uvicorn app:app --reload --port 8000
```

**Terminal 2 - Start Streamlit Frontend**:
```bash
streamlit run client.py
```

### Method 2: Single Command
```bash
# Start backend in background, then frontend
uvicorn app:app --reload --port 8000 & streamlit run client.py
```

Access the application at: `http://localhost:8501`

## Example Queries

### Company Search Examples

| Query | Expected Output | Use Case |
|-------|----------------|----------|
| `"Find AI companies in San Francisco"` | List of AI/ML companies in SF with industry, size, location | Market research |
| `"Show me fintech startups with more than 100 employees"` | Fintech companies filtered by size | Investment analysis |
| `"Chemical companies with polymer research in Germany"` | German chemical companies with polymer focus | Industry targeting |
| `"Find SaaS companies in Europe"` | European SaaS companies with websites and details | Sales prospecting |

### Employee Search Examples

| Query | Expected Output | Use Case |
|-------|----------------|----------|
| `"Find Python developers at Google"` | Google employees with Python skills | Talent sourcing |
| `"Show me data scientists with machine learning experience"` | ML-focused data scientists with connections | Recruitment |
| `"Find senior engineers at Microsoft in Seattle"` | Senior Microsoft engineers in Seattle area | Competitive analysis |
| `"LLM engineers with QLoRA fine-tuning experience"` | Specialists in LLM fine-tuning techniques | Technical hiring |

### Advanced Query Examples

| Main Query | Refinement | Combined Result |
|------------|------------|----------------|
| `"Find tech companies"` | `"Europe, more than 500 employees"` | Large European tech companies |
| `"Show me engineers"` | `"AI/ML background, San Francisco"` | SF-based AI/ML engineers |
| `"Find pharmaceutical companies"` | `"drug discovery, Boston area"` | Boston pharma companies in drug discovery |

## Features in Detail

### Smart Query Processing
- Automatically detects if query is about companies or employees
- Converts natural language to structured API filters
- Handles location, industry, skills, and size parameters

### Advanced UI Features
- **Multi-level Highlighting**: Top results (green), skill matches (orange/purple), high connections/size (blue)
- **Dynamic Filtering**: Filter results by location, size, connections
- **Theme Toggle**: Switch between light and dark modes
- **Export Options**: Download results in multiple formats

### AI Summarization
- Provides intelligent summaries of search results
- Highlights most relevant matches
- Contextual insights based on query intent

## API Endpoints

### POST `/sourcing`
Main search endpoint that processes queries and returns results.

**Request Body**:
```json
{
  "user_query": "Find AI companies in Silicon Valley",
  "refinement_query": "more than 200 employees"
}
```

**Response**:
```json
{
  "query_type": "company",
  "results": [
    {
      "Name": "OpenAI",
      "Industry": "Artificial Intelligence",
      "Size": "500-1000",
      "Location": "United States",
      "Website": "openai.com"
    }
  ],
  "ai_summary": "Found 15 AI companies in Silicon Valley..."
}
```

## Troubleshooting

### Common Issues

1. **"Connection refused" error**:
   - Ensure FastAPI backend is running on port 8000
   - Check if port is already in use

2. **"No results found"**:
   - Verify API keys in `.env` file
   - Check Coresignal API quota/limits
   - Try broader search terms

3. **Import errors**:
   - Reinstall dependencies: `pip install -r requirements.txt`
   - Check Python version compatibility

### Performance Tips
- Use specific queries for better results
- Combine main query with refinements for precision
- Export large result sets for offline analysis

## Contributing

Feel free to submit issues and enhancement requests!
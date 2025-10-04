# AI-Powered Sourcing Agent

An intelligent sourcing assistant that uses AI to find companies and employees through natural language queries. Built with Streamlit frontend, powered by Groq LLM and Coresignal API.

## 🚀 Quick Start

1. **Configure API Keys**: Add your API keys in the Hugging Face Spaces secrets:
   - `GROQ_API_KEY`: Your Groq API key
   - `CORESIGNAL_API_KEY`: Your Coresignal API key

2. **Start Searching**: Enter natural language queries like:
   - "Find AI companies in San Francisco"
   - "Show me Python developers at Google"
   - "Find fintech startups with more than 100 employees"

## Features

- 🤖 Natural language query processing with Groq LLM
- 🏢 Company and employee search via Coresignal API
- 🎨 Interactive Streamlit UI with dark/light theme
- 📊 Advanced filtering and multi-level result highlighting
- 📁 Export results to CSV, Excel, and PDF formats
- 🔍 AI-powered result summarization

## Example Queries

### Company Search
- "Find AI companies in San Francisco"
- "Show me fintech startups with more than 100 employees"
- "Chemical companies with polymer research in Germany"

### Employee Search
- "Find Python developers at Google"
- "Show me data scientists with machine learning experience"
- "Find senior engineers at Microsoft in Seattle"

## Configuration

This app requires two API keys to be configured in Hugging Face Spaces secrets:

1. **GROQ_API_KEY**: Get from [Groq Console](https://console.groq.com/)
2. **CORESIGNAL_API_KEY**: Get from [Coresignal](https://coresignal.com/)

## Local Development

For local development, see the main README.md file for FastAPI + Streamlit setup instructions.
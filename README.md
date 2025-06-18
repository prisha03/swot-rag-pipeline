# Competitor Intelligence Suite

This project started as a capstone, but evolved into something closer to a product.

The **Competitor Intelligence Suite** is a complete analytics tool that reads through corporate transcripts, pulls official financial data, monitors stock trends, and delivers both strategic insights and forward-looking forecasts. It’s designed for analysts and decision-makers who want to move from raw data to real answers — fast.

I built it to mirror what an in-house analytics product at a consulting firm or investment team might do, without needing multiple tools or licenses.


## What it does

- **Turns unstructured transcripts into boardroom-ready SWOT insights**
- **Connects narrative data to financial performance** (via SEC and Yahoo Finance)
- **Uses statistical forecasting (ARIMAX) to predict next-quarter returns**
- **Builds downloadable reports (PDF & CSV) for instant sharing**
- All through a **clean Streamlit interface** that works offline

## Why it matters

Companies say a lot in their earnings calls. Some of it is noise.  
But some of it foreshadows movement — in performance, in stock price, in strategy.

This app doesn’t just summarise what was said. It:
- Measures sentiment over time  
- Tracks mentions of key business units (buzz)  
- Tags risks, opportunities, and strategic moves using RAG + LLMs  
- Checks which variables (text, sentiment, financials) correlate with actual stock movement

Then it models the signal and forecasts forward.

In other words, **it connects the story to the stock.**


## How it works (in plain English)

1. **You upload a transcript** (PDF or TXT)
2. The system breaks it into readable chunks
3. It asks smart questions like “What are the strengths?” and uses a local AI model to answer them
4. It finds supporting quotes, so you're never guessing where the insight came from
5. It saves everything in a polished PDF
6. Meanwhile, it also pulls the company’s financials (from the SEC), stock history, and text-based sentiment
7. It tests what variables might actually influence returns
8. Finally, it builds a predictive ARIMAX model and shows a forecast


## Built with

- **LLM + Retrieval**: SentenceTransformers, FAISS, Ollama (LLaMA 3)
- **Forecasting**: statsmodels, ARIMAX, Granger causality
- **Data ingestion**: SEC API, Yahoo Finance, custom transcript parsers
- **Interface**: Streamlit
- **Reporting**: FPDF for downloadable PDFs


## Example use case

Imagine uploading `UNH_Q1_2024.pdf`  
→ You get:

- 3–4 focused SWOT bullets per category, backed by exact quotes  
- A clean PDF you could walk into a client meeting with  
- A sentiment/buzz trend showing concern or confidence over time  
- Financials pulled straight from SEC filings  
- A predictive chart showing the next 4 quarters of expected stock movement  

It’s not just analysis. It’s explanation, direction, and justification — in one tool.


## How to run it

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.com) installed locally (to run LLaMA 3 offline)
- Internet for financial data APIs


### Setup

```bash
git clone https://github.com/your-username/competitor-intelligence-suite.git
cd competitor-intelligence-suite
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

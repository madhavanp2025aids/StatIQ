# StatGPT 📊
### AI Assistant for Official Indian Statistics (MoSPI)

StatGPT is a full-stack AI application that answers questions about official Indian government statistics from the **Ministry of Statistics and Programme Implementation (MoSPI)** — with source attribution, data tables, and charts.

---

## Features

- 🔍 **Natural language queries** — ask in plain English
- 📋 **Structured data retrieval** from PLFS, CPI, NAS, IIP, ASI datasets
- 📈 **Auto-generated charts** for trends and comparisons
- 🏷️ **Source attribution** — every answer cites the official MoSPI document
- 💬 **Conversation memory** — multi-turn question & answer
- 🛡️ **Hallucination prevention** — LLM only uses retrieved data

---

## Quick Start

### 1. Prerequisites
- Python 3.11+
- A free Gemini API key from [aistudio.google.com](https://aistudio.google.com)

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API key
Open `.env` and replace the placeholder:
```
GEMINI_API_KEY=your_actual_key_here
```

### 4. Run the server
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Open the app
Navigate to [http://localhost:8000](http://localhost:8000) in your browser.

---

## Project Structure

```
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI app + routes
│   ├── agent.py         # LLM agent (Gemini integration)
│   ├── data_loader.py   # JSON dataset loader & query helpers
│   └── system_prompt.py # StatGPT system prompt
│
├── data/
│   ├── plfs.json        # Periodic Labour Force Survey (2017-18 to 2023-24)
│   ├── cpi.json         # Consumer Price Index (2019–2024, monthly)
│   ├── nas.json         # National Accounts Statistics (GDP/GVA)
│   ├── iip.json         # Index of Industrial Production
│   ├── asi.json         # Annual Survey of Industries
│   └── metadata.json    # Dataset catalog & indicators
│
├── frontend/
│   ├── index.html       # Single-page app
│   ├── style.css        # Dark glassmorphism design
│   └── app.js           # Chat UI, Chart.js, API calls
│
├── .env                 # API key (fill in before running)
├── requirements.txt
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the frontend |
| `GET` | `/health` | Health check |
| `POST` | `/chat` | Send a message, get structured response |
| `POST` | `/reset` | Clear conversation history |
| `GET` | `/datasets` | List all available datasets |
| `GET` | `/datasets/{name}` | Get raw dataset (plfs/cpi/nas/iip/asi) |

### Chat request format
```json
{
  "message": "What is the unemployment rate in rural India for 2023-24?",
  "session_reset": false
}
```

### Chat response format
```json
{
  "answer": "...",
  "data_table": [...],
  "interpretation": "...",
  "source": "PLFS Annual Report 2023-24, MoSPI, Table A-1",
  "chart_config": { "type": "bar", "labels": [...], "datasets": [...] }
}
```

---

## Data Sources

All data is sourced from official MoSPI publications:

| Dataset | Source Document |
|---------|----------------|
| PLFS    | PLFS Annual Reports 2017-18 to 2023-24, MoSPI |
| CPI     | Monthly CPI Press Releases, MoSPI |
| NAS     | National Accounts Statistics 2024, MoSPI |
| IIP     | Monthly IIP Press Releases, MoSPI |
| ASI     | ASI Annual Summary Results, MoSPI |

> ⚠️ **Note**: The JSON files contain seed data based on publicly available MoSPI publications for demonstration. For production use, replace with the latest official downloads from [mospi.gov.in](https://mospi.gov.in).

---

## Disclaimer

This application is an independent educational tool. It is not affiliated with, endorsed by, or an official product of the Ministry of Statistics and Programme Implementation, Government of India.

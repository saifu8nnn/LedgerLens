<p align="center">
  <svg width="200" height="200" viewBox="0 0 1000 1000" xmlns="http://www.w3.org/2000/svg">
    <g fill="#3b82f6"> <path d="M150 150 H650 V300 H400 V850 H150 Z"/>
      <path d="M450 600 H700 V300 H850 V850 H450 Z"/>
    </g>
  </svg>
</p>

<h1 align="center">LedgerLens</h1>
<p align="center"><b>AI-Powered Enterprise 3-Way Match Audit Engine</b></p>

Enterprises lose millions of dollars annually to "procurement leakage"—vendor price hikes, unauthorized quantity padding, and fraudulent line items buried inside unstructured PDF invoices. 

**LedgerLens** automates the historically manual "Stare and Compare" audit process. By bridging generative AI with deterministic relational databases, LedgerLens catches every penny of overcharge in milliseconds.

---

## ⚙️ How It Works (The Architecture)
We don't use LLMs to do math (they hallucinate). We use them solely as a parsing layer, leaving the financial security to a strict PostgreSQL database.

1. **Extraction (AI Layer):** A vendor PDF is uploaded. We use the Groq API (Llama-3.1-8b-instant) with `temperature=0.0` to extract the unstructured text into a strict, validated JSON schema.

2. **Validation (Data Layer):** The backend queries the enterprise's PostgreSQL database for the internal, pre-approved Purchase Order (PO).

3. **Execution (Logic Layer):** A deterministic Python algorithm calculates discrepancies (`billed_price > approved_price` or `billed_qty > approved_qty`), flags unauthorized items, and outputs the exact Rupee (₹) leakage.

---

## 📂 Repository Structure
```text
LedgerLens/
│
├── backend/                  # FastAPI & PostgreSQL Engine
│   ├── app/
│   │   ├── main.py           # Core AI & Routing logic
│   │   ├── database.py       # SQLAlchemy Postgres connections
│   │   └── models.py         # DB Schemas (Purchase Orders)
│   ├── requirements.txt      
│   └── .env                  # API Keys & DB URLs
│
├── frontend/                 # Single-Page Application (SPA)
│   └── index.html            # Dashboard UI (HTML/CSS/Vanilla JS)
│
└── test_invoices/            # 5 Scenarios for live testing
```
## 🗄️ A Note on the "Seed Database"
To demonstrate this MVP without requiring access to a live corporate ERP system (like SAP or Oracle), the PostgreSQL database is automatically populated via a seed_db function on startup.

This creates a mock "Approved Purchase Order" inventory containing servers, monitors, and laptops. In a production environment, this seed script would be replaced by a secure Cron job or Webhook that syncs daily with the enterprise's actual internal ERP system.

## 🚀 Deployment & Local Setup

1. Database (Docker)
Ensure Docker Desktop is running, then spin up the PostgreSQL container:

Bash
docker run --name ledgerlens-db -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=securepass -e POSTGRES_DB=ledgerlens -p 5432:5432 -d postgres:15-alpine
2. Backend (FastAPI)
Navigate to the backend/ directory, set up your .env file with your GROQ_API_KEY, and launch the server:

Bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
The backend will automatically create the tables and seed the PO data.

3. Frontend (UI)
The frontend is built as a zero-dependency HTML dashboard for rapid deployment. Simply open frontend/index.html in any modern web browser. It is configured to communicate via CORS with http://127.0.0.1:8000.

## 🧪 Testing the Engine (The 5 Scenarios)
We have provided 5 distinct PDFs in the repository to test the engine's edge cases. Upload these via the frontend UI to see the audit in action:

🟢 INV_001_Perfect_Match.pdf: Vendor bills exactly what was approved. Result: PASSED.

🔴 INV_002_Price_Overcharge.pdf: Vendor sneaks a ₹3,000 markup on monitors. Result: FAILED (Price Leakage calculated).

🔴 INV_003_Quantity_Padding.pdf: Vendor ships 18 items when only 15 were ordered. Result: FAILED (Quantity Leakage calculated).

🔴 INV_004_Total_Fraud.pdf: Vendor bills for luxury items never requested. Result: FAILED (FRAUD Flagged).

🔴 INV_005_The_Disaster.pdf: A combination of price hikes, quantity leaks, and unknown items. Result: FAILED (Complete itemized breakdown).
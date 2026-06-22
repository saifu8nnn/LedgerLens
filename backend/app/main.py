import os
import json
import pdfplumber
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, get_db
from .models import PurchaseOrder


load_dotenv()



Base.metadata.create_all(bind=engine)

app = FastAPI(title="LedgerLens AI 3-Way Match Audit Engine")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

@app.on_event("startup")
def seed_db():
    db = next(get_db())
    
    
    sample_pos = [
        PurchaseOrder(item_name="Lenovo ThinkPad L14", approved_quantity=50, approved_price=85000.0),
        PurchaseOrder(item_name="Ergonomic Office Chair", approved_quantity=100, approved_price=4500.0),
        PurchaseOrder(item_name="Wireless Mouse", approved_quantity=200, approved_price=1200.0),
        PurchaseOrder(item_name="Dell PowerEdge R740 Server", approved_quantity=5, approved_price=350000.0),
        PurchaseOrder(item_name="27-inch 4K Monitor", approved_quantity=50, approved_price=22000.0),
        PurchaseOrder(item_name="Enterprise Cloud License (Annual)", approved_quantity=20, approved_price=65000.0),
        PurchaseOrder(item_name="Motorized Standing Desk", approved_quantity=30, approved_price=18500.0),
        PurchaseOrder(item_name="Cisco Meraki MR46 Access Point", approved_quantity=15, approved_price=42000.0)
    ]
    
    
    for po in sample_pos:
        existing_item = db.query(PurchaseOrder).filter(PurchaseOrder.item_name == po.item_name).first()
        if not existing_item:
            db.add(po)
            
    db.commit()
    db.close()

@app.post("/audit-invoice")
async def audit_invoice(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # 1. Extract Text from PDF
    try:
        with pdfplumber.open(file.file) as pdf:
            text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read PDF: {str(e)}")

    # 2. Call AI parsing layer via Groq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "YOUR_REAL_GROQ_API_KEY_HERE":
        raise HTTPException(status_code=500, detail="Groq API Key is missing from .env configuration.")

    client = Groq(api_key=api_key)
    system_prompt = """You are a precise data extraction API. 
    Extract the line items from the provided invoice text.
    Return ONLY a raw, valid JSON array of objects without markdown backticks.
    Each object must exactly use these keys: "item_name", "billed_quantity", "billed_price".
    Ensure numbers are formatted correctly (quantities as integers, prices as floats)."""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.0 # Force zero creativity for strict data extraction
        )
        ai_response = chat_completion.choices[0].message.content.strip()
        
        # Strip code fences if the AI hallucinates markdown formatting
        if ai_response.startswith("```json"): 
            ai_response = ai_response[7:-3]
        elif ai_response.startswith("```"): 
            ai_response = ai_response[3:-3]
        
        invoice_items = json.loads(ai_response)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"AI returned invalid JSON: {ai_response}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Extraction Layer Error: {str(e)}")

    # 3. Running Deterministic 3-Way Match Audit Math against PostgreSQL
    audit_report = {"status": "PASSED - NO LEAKS", "total_overcharge_rupees": 0.0, "flags": []}

    for item in invoice_items:
        # Clean the extracted name to prevent trailing space bugs
        extracted_name = item.get("item_name", "").strip()
        
        # Query PostgreSQL database for matching PO record
        po_record = db.query(PurchaseOrder).filter(PurchaseOrder.item_name == extracted_name).first()

        if not po_record:
            audit_report["flags"].append({
                "item": extracted_name if extracted_name else "Unknown", 
                "error": "FRAUD: Item not found in approved PO database."
            })
            audit_report["status"] = "FAILED - DISCREPANCIES FOUND"
            continue

        po_qty = po_record.approved_quantity
        po_price = po_record.approved_price
        
        billed_qty = item.get("billed_quantity", 0)
        billed_price = item.get("billed_price", 0.0)

        # The Validation Engine Logic
        if billed_price > po_price or billed_qty > po_qty:
            audit_report["status"] = "FAILED - DISCREPANCIES FOUND"
            
            # Calculate financial leak exactly
            expected_cost = min(billed_qty, po_qty) * po_price
            actual_billed = billed_qty * billed_price
            leakage = max(0.0, actual_billed - expected_cost)
            
            audit_report["total_overcharge_rupees"] += leakage
            
            audit_report["flags"].append({
                "item": extracted_name,
                "issue": "Overcharge Detected",
                "leakage_amount_rupees": leakage,
                "details": {
                    "approved": f"{po_qty} units @ ₹{po_price}", 
                    "billed": f"{billed_qty} units @ ₹{billed_price}"
                }
            })

    return {
        "ai_extracted_data": invoice_items, 
        "database_audit_results": audit_report
    }
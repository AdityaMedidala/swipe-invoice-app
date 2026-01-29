import io
import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from typing import List

# Import your local modules
from docai import process_document
from llm import normalize_invoice, extract_bulk_invoices
from validator import validate_invoice

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def map_to_frontend_schema(data: dict) -> dict:
    """
    Maps backend Python dicts (snake_case) to Frontend JSON (camelCase).
    """
    
    # 1. Map Items
    mapped_items = []
    for item in data.get("items", []):
        # Generate a stable temporary ID for the row
        item_id = str(pd.util.hash_pandas_object(pd.Series([item.get("name")]), index=False)[0])
        
        mapped_items.append({
            "id": item_id,
            "name": item.get("name"),
            "quantity": item.get("quantity", 0),
            "unitPrice": item.get("unit_price", 0),
            "tax": item.get("tax", 0),
            "amount": item.get("amount", 0),
            "priceWithTax": item.get("price_with_tax", 0)
        })

    # 2. Map Bank Details (FIXED)
    # Python (snake_case) -> Frontend (camelCase)
    bank_raw = data.get("bank", {})
    bank_mapped = {
        "bankName": bank_raw.get("bank_name"),
        "accountNumber": bank_raw.get("account_number"),
        "ifsc": bank_raw.get("ifsc") or bank_raw.get("ifsc_code"), # Handle variations
        "branch": bank_raw.get("branch")
    }

    # 3. Map Invoice Structure
    return {
        "invoiceId": data.get("invoice_id"),
        "serialNumber": data.get("invoice_id"),
        "date": data.get("date"),
        "customerName": data.get("customer", {}).get("name"),
        "customerPhone": data.get("customer", {}).get("phone"),
        
        "totalAmount": data.get("total", 0),
        "taxAmount": data.get("tax_total", 0),
        
        # --- ADDED THIS FIELD ---
        "totalInWords": data.get("total_in_words"),
        # ------------------------

        "bankDetails": bank_mapped, # Uses the fixed mapping
        
        "items": mapped_items,
        "isConsistent": data.get("is_consistent", True),
        "missingFields": data.get("missing_fields", [])
    }

@app.post("/api/extract-batch")
async def extract_batch(files: List[UploadFile] = File(...)):
    results = []
    
    for file in files:
        try:
            content = await file.read()
            raw_invoices = []

            # A. Handle Excel
            if file.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(content))
                # Ensure all columns are strings to prevent JSON errors
                csv_text = df.astype(str).to_csv(index=False)
                bulk_data = extract_bulk_invoices(csv_text)
                raw_invoices = bulk_data.get("invoices", [])

            # B. Handle PDF / Images
            else:
                doc = process_document(content, file.content_type)
                # Pass both text and entities to LLM
                entities = [{"type": e.type_, "text": e.mention_text} for e in doc.entities]
                single_data = normalize_invoice(doc.text, entities)
                raw_invoices = [single_data]

            # C. Validate & Map
            for inv in raw_invoices:
                clean_inv = validate_invoice(inv)
                frontend_data = map_to_frontend_schema(clean_inv)
                
                results.append({
                    "filename": file.filename,
                    "invoice": frontend_data,
                    "status": "success"
                })

        except Exception as e:
            print(f"Error processing {file.filename}: {str(e)}")
            results.append({
                "filename": file.filename,
                "error": str(e),
                "status": "failed"
            })

    return {"count": len(results), "results": results}
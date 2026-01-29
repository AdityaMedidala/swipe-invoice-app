import io
import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import documentai_v1 as documentai

from docai import process_document
from llm import normalize_invoice, extract_bulk_invoices
from validator import validate_invoice
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def map_to_frontend_schema(data: dict) -> dict:
    print("\n---------- MAIN.PY: map_to_frontend_schema() STARTED ----------")
    print(f"[MAPPER] Input data keys: {list(data.keys())}")
    print(f"[MAPPER] Input data:\n{data}")
    
    is_consistent = data.get("is_consistent", True)
    subtotal_check = data.get("subtotal", 0)
    grand_total = data.get("total", 0)
    variance = abs(grand_total - subtotal_check)
    
    print(f"[MAPPER] is_consistent: {is_consistent}")
    print(f"[MAPPER] subtotal_check: {subtotal_check}")
    print(f"[MAPPER] grand_total: {grand_total}")
    print(f"[MAPPER] variance: {variance}")

    result = {
        "invoiceId": data.get("invoice_id"),
        "serialNumber": data.get("invoice_id"),
        "date": data.get("date"),
        "isConsistent": is_consistent,
        "missingFields": data.get("missing_fields", []),
        "variance": round(variance, 2),
        "customerName": data.get("customer", {}).get("name"),
        "customerPhone": data.get("customer", {}).get("phone"),
        "totalAmount": data.get("total", 0),
        "taxAmount": data.get("tax_total", 0),
        "totalInWords": data.get("amount_in_words"),
        "bankDetails": {
            "bankName": data.get("bank", {}).get("name"),
            "accountNumber": data.get("bank", {}).get("account"),
            "ifsc": data.get("bank", {}).get("ifsc"),
            "branch": data.get("bank", {}).get("branch"),
        },
        "items": [
            {
                "productId": f"prod-{i}",
                "itemName": item.get("name"),
                "quantity": item.get("qty"),
                "unitPrice": item.get("unit_price"),
                "taxAmount": item.get("tax"),
                "amount": item.get("total"),
            }
            for i, item in enumerate(data.get("items", []))
        ],
    }
    
    print(f"[MAPPER] Output invoiceId: {result['invoiceId']}")
    print(f"[MAPPER] Output date: {result['date']}")
    print(f"[MAPPER] Output customerName: {result['customerName']}")
    print(f"[MAPPER] Output totalAmount: {result['totalAmount']}")
    print(f"[MAPPER] Output taxAmount: {result['taxAmount']}")
    print(f"[MAPPER] Output items count: {len(result['items'])}")
    print(f"[MAPPER] Output missingFields: {result['missingFields']}")
    print(f"[MAPPER] Full mapped result:\n{result}")
    print("---------- MAIN.PY: map_to_frontend_schema() COMPLETED ----------\n")
    
    return result

@app.post("/api/extract")
async def extract_invoice(file: UploadFile = File(...)):
    print("\n" + "="*80)
    print("========== MAIN.PY: /api/extract ENDPOINT CALLED ==========")
    print("="*80)
    print(f"[EXTRACT] File received: {file.filename}")
    print(f"[EXTRACT] Content type: {file.content_type}")
    print(f"[EXTRACT] File size: {file.size if hasattr(file, 'size') else 'Unknown'}")
    
    content = await file.read()
    print(f"[EXTRACT] Content read: {len(content)} bytes")
    
    # === PATH A: EXCEL FILES (BULK) ===
    if file.content_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel", "text/csv"]:
        print(f"\n[EXTRACT] 📊 PATH A: Processing as EXCEL/CSV file")
        print(f"--- Processing Bulk Excel: {file.filename} ---")
        try:
            if file.content_type == "text/csv":
                print("[EXTRACT] Reading as CSV...")
                df = pd.read_csv(io.BytesIO(content))
            else:
                print("[EXTRACT] Reading as Excel...")
                df = pd.read_excel(io.BytesIO(content))
            
            print(f"[EXTRACT] DataFrame shape: {df.shape}")
            print(f"[EXTRACT] DataFrame columns: {list(df.columns)}")
            print(f"[EXTRACT] DataFrame preview:\n{df.head()}")
            
            csv_text = df.to_csv(index=False)
            print(f"[EXTRACT] Converted to CSV text: {len(csv_text)} characters")
            
            print("[EXTRACT] Calling extract_bulk_invoices()...")
            bulk_data = extract_bulk_invoices(csv_text)
            print(f"[EXTRACT] extract_bulk_invoices() returned: {type(bulk_data)}")
            
            raw_invoices = bulk_data.get("invoices", [])
            print(f"[EXTRACT] Number of raw invoices: {len(raw_invoices)}")
            
        except Exception as e:
            print(f"[EXTRACT] ❌ EXCEL ERROR: {str(e)}")
            import traceback
            print(f"[EXTRACT] Traceback:\n{traceback.format_exc()}")
            return {"error": f"Excel Error: {str(e)}"}

    # === PATH B: PDF/IMAGES (SINGLE) ===
    else:
        print(f"\n[EXTRACT] 📄 PATH B: Processing as PDF/IMAGE file")
        print(f"--- Processing PDF/Image: {file.filename} ---")
        
        print("[EXTRACT] Calling process_document()...")
        doc = process_document(content, file.content_type)
        print(f"[EXTRACT] Document processed, type: {type(doc)}")
        
        print("[EXTRACT] Converting document to dict...")
        doc_dict = documentai.Document.to_dict(doc, preserving_proto_field_name=True)
        print(f"[EXTRACT] Document dict keys: {list(doc_dict.keys())}")
        
        entities = doc_dict.get("entities", [])
        print(f"[EXTRACT] Number of entities: {len(entities)}")
        
        raw_text = doc.text
        print(f"[EXTRACT] Raw text length: {len(raw_text)} characters")
        print(f"[EXTRACT] Raw text preview (first 300 chars):\n{raw_text[:300]}")
        
        print("[EXTRACT] Calling normalize_invoice()...")
        single_data = normalize_invoice(raw_text, entities)
        print(f"[EXTRACT] normalize_invoice() returned: {type(single_data)}")
        print(f"[EXTRACT] Single data keys: {list(single_data.keys())}")
        
        # Use a list so processing logic is shared
        raw_invoices = [single_data]
        print(f"[EXTRACT] Wrapped in list: {len(raw_invoices)} invoice(s)")

    # === COMMON VALIDATION & MAPPING ===
    print(f"\n[EXTRACT] 🔍 Starting validation & mapping for {len(raw_invoices)} invoice(s)...")
    processed_results = []
    
    for idx, inv in enumerate(raw_invoices):
        print(f"\n[EXTRACT] Processing invoice {idx + 1}/{len(raw_invoices)}...")
        print(f"[EXTRACT] Invoice {idx + 1} raw data:\n{inv}")
        
        print(f"[EXTRACT] Calling validate_invoice() for invoice {idx + 1}...")
        clean_inv = validate_invoice(inv)
        print(f"[EXTRACT] validate_invoice() returned for invoice {idx + 1}")
        print(f"[EXTRACT] Clean invoice {idx + 1} data:\n{clean_inv}")
        
        print(f"[EXTRACT] Calling map_to_frontend_schema() for invoice {idx + 1}...")
        frontend_inv = map_to_frontend_schema(clean_inv)
        print(f"[EXTRACT] Frontend invoice {idx + 1} mapped successfully")
        
        processed_results.append(frontend_inv)
        print(f"[EXTRACT] Added invoice {idx + 1} to results")

    # === RETURN BOTH FORMATS (FIXES FRONTEND BREAK) ===
    response = {
        "invoice": processed_results[0] if processed_results else {}, # Backward compatibility
        "invoices": processed_results # Forward compatibility (Excel)
    }
    
    print(f"\n[EXTRACT] 📤 FINAL RESPONSE:")
    print(f"[EXTRACT] Total processed invoices: {len(processed_results)}")
    print(f"[EXTRACT] Response structure: {list(response.keys())}")
    print(f"[EXTRACT] Full response:\n{response}")
    print("="*80)
    print("========== MAIN.PY: /api/extract ENDPOINT COMPLETED ==========")
    print("="*80 + "\n")
    
    return response


@app.post("/api/extract-batch")
async def extract_invoices_batch(files: List[UploadFile] = File(...)):
    print("\n" + "="*80)
    print("========== MAIN.PY: /api/extract-batch ENDPOINT CALLED ==========")
    print("="*80)
    print(f"[BATCH] Number of files received: {len(files)}")
    for idx, f in enumerate(files):
        print(f"[BATCH] File {idx + 1}: {f.filename} ({f.content_type})")

    results = []

    for file_idx, file in enumerate(files):
        print(f"\n[BATCH] {'='*60}")
        print(f"[BATCH] Processing file {file_idx + 1}/{len(files)}: {file.filename}")
        print(f"[BATCH] {'='*60}")

        try:
            content = await file.read()
            print(f"[BATCH] Content read: {len(content)} bytes")

            # ========= EXCEL / CSV =========
            if (
                file.content_type in [
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "application/vnd.ms-excel",
                    "text/csv"]
                     or 
                    file.filename.lower().endswith((".xlsx", ".xls", ".csv"))
                    ):
                print(f"[BATCH] 📊 Detected as EXCEL/CSV")
                
                if file.content_type == "text/csv":
                    print(f"[BATCH] Reading as CSV...")
                    df = pd.read_csv(io.BytesIO(content))
                else:
                    print(f"[BATCH] Reading as Excel...")
                    df = pd.read_excel(io.BytesIO(content))

                print(f"[BATCH] DataFrame shape: {df.shape}")
                print(f"[BATCH] DataFrame columns: {list(df.columns)}")
                
                csv_text = df.to_csv(index=False)
                print(f"[BATCH] Converted to CSV: {len(csv_text)} characters")

                print(f"[BATCH] Calling extract_bulk_invoices()...")
                bulk_data = extract_bulk_invoices(csv_text)

                raw_invoices = bulk_data.get("invoices", [])
                print(f"[BATCH] Extracted {len(raw_invoices)} invoices from Excel")

            # ========= PDF / IMAGE =========
            else:
                print(f"[BATCH] 📄 Detected as PDF/IMAGE")

                print(f"[BATCH] Calling process_document()...")
                doc = process_document(content, file.content_type)

                print(f"[BATCH] Converting to dict...")
                doc_dict = documentai.Document.to_dict(
                    doc,
                    preserving_proto_field_name=True
                )

                entities = doc_dict.get("entities", [])
                print(f"[BATCH] Entities found: {len(entities)}")
                
                raw_text = doc.text
                print(f"[BATCH] Text length: {len(raw_text)} characters")

                print(f"[BATCH] Calling normalize_invoice()...")
                single_data = normalize_invoice(raw_text, entities)

                raw_invoices = [single_data]
                print(f"[BATCH] Created single invoice object")

            # ========= VALIDATION =========
            print(f"[BATCH] Validating {len(raw_invoices)} invoice(s)...")
            
            for inv_idx, inv in enumerate(raw_invoices):
                print(f"\n[BATCH] Validating invoice {inv_idx + 1}/{len(raw_invoices)}...")
                print(f"[BATCH] Raw invoice data:\n{inv}")

                print(f"[BATCH] Calling validate_invoice()...")
                clean = validate_invoice(inv)
                print(f"[BATCH] Validation complete")

                print(f"[BATCH] Calling map_to_frontend_schema()...")
                mapped = map_to_frontend_schema(clean)
                print(f"[BATCH] Mapping complete")

                result_obj = {
                    "filename": file.filename,
                    "invoice": mapped,
                    "status": "success"
                }
                
                results.append(result_obj)
                print(f"[BATCH] ✅ Added success result for {file.filename}")
                print(f"[BATCH] Result object:\n{result_obj}")

        except Exception as e:
            print(f"[BATCH] ❌ ERROR processing {file.filename}: {str(e)}")
            import traceback
            print(f"[BATCH] Traceback:\n{traceback.format_exc()}")

            error_obj = {
                "filename": file.filename,
                "error": str(e),
                "status": "failed"
            }
            
            results.append(error_obj)
            print(f"[BATCH] Added error result for {file.filename}")

    final_response = {
        "count": len(results),
        "results": results
    }
    
    print(f"\n[BATCH] 📤 FINAL BATCH RESPONSE:")
    print(f"[BATCH] Total results: {len(results)}")
    print(f"[BATCH] Success count: {sum(1 for r in results if r.get('status') == 'success')}")
    print(f"[BATCH] Failed count: {sum(1 for r in results if r.get('status') == 'failed')}")
    print(f"[BATCH] Full response:\n{final_response}")
    print("="*80)
    print("========== MAIN.PY: /api/extract-batch ENDPOINT COMPLETED ==========")
    print("="*80 + "\n")

    return final_response
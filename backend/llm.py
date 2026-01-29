import os
import json
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# --- PDF FUNCTION (Fixed Tax Extraction) ---
def normalize_invoice(raw_text: str, entities: list) -> dict:
    print("\n========== LLM.PY: normalize_invoice() STARTED ==========")
    print(f"[LLM] Raw text length: {len(raw_text)} characters")
    print(f"[LLM] Number of entities: {len(entities)}")
    print(f"[LLM] Entities preview: {json.dumps(entities[:3], indent=2) if entities else 'None'}")
    
    prompt = f"""
    You are an expert financial data extractor.
    
    CRITICAL GOAL: Extract a valid JSON object.
    
    INSTRUCTIONS FOR ITEMS:
    1. Extract all products from the item table.
    2. 'unit_price' = Rate/Item column value (price per unit before tax).
    3. 'tax' = GST/Tax column value. Extract ONLY the tax amount number.
       Examples: 
       - "238.10 (5%)" → tax = 238.10
       - "18%" with Amount 90169.49 and Taxable 90169.49 → calculate: tax = 0
       - CGST 9.0% 8115.25 → tax = 8115.25
    4. 'total' = Amount/Final column (the rightmost price column for each item).
    5. 'qty' = Quantity column value.
    6. Include "Making charges", "debit card charges", "Shipping Charges" as separate items with qty=1.
    
    CRITICAL TAX RULES:
    - If tax is shown PER ITEM in the table (like "238.10 (5%)"), extract it for that item
    - If tax is shown only as INVOICE TOTALS (CGST/SGST/IGST at bottom), set item tax = 0
    - For Making/Shipping charges with no tax info, set tax = 0
    - Always capture "tax_total" from the CGST+SGST or IGST total at invoice level
    
    EXAMPLES:
    - Invoice shows "CGST 9.0% 8,115.25" and "SGST 9.0% 8,115.25" → tax_total = 16230.50, item tax = 0
    - Item row shows "238.10 (5%)" in GST column → that item's tax = 238.10

    SCHEMA:
    {{
      "invoice_id": string,
      "date": string,
      "amount_in_words": string|null,
      "customer": {{
        "name": string|null,
        "phone": string|null
      }},
      "bank": {{
        "name": string|null,
        "account": string|null,
        "ifsc": string|null,
        "branch": string|null
      }},
      "items": [
        {{
          "name": string,
          "qty": number,
          "unit_price": number,
          "tax": number,
          "total": number
        }}
      ],
      "subtotal": number,
      "tax_total": number,
      "total": number
    }}

    OCR TEXT:
    {raw_text}

    ENTITIES:
    {json.dumps(entities, indent=2)}
    """

    print("[LLM] Sending prompt to Gemini API...")
    print(f"[LLM] Prompt length: {len(prompt)} characters")
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    print("[LLM] Received response from Gemini")
    text = response.text.strip()
    print(f"[LLM] Response text length: {len(text)} characters")
    print(f"[LLM] Raw response preview (first 500 chars):\n{text[:500]}")
    
    match = re.search(r"\{.*\}", text, re.DOTALL)
    clean_text = match.group(0) if match else text
    print(f"[LLM] JSON extraction {'successful' if match else 'FAILED - using raw text'}")
    print(f"[LLM] Clean text preview (first 300 chars):\n{clean_text[:300]}")

    try:
        result = json.loads(clean_text)
        print("[LLM] ✅ JSON parsing SUCCESSFUL")
        print(f"[LLM] Extracted invoice_id: {result.get('invoice_id')}")
        print(f"[LLM] Extracted date: {result.get('date')}")
        print(f"[LLM] Extracted customer name: {result.get('customer', {}).get('name')}")
        print(f"[LLM] Number of items: {len(result.get('items', []))}")
        print(f"[LLM] Subtotal: {result.get('subtotal')}")
        print(f"[LLM] Tax total: {result.get('tax_total')}")
        print(f"[LLM] Grand total: {result.get('total')}")
        print(f"[LLM] Full result:\n{json.dumps(result, indent=2)}")
        print("========== LLM.PY: normalize_invoice() COMPLETED ==========\n")
        return result
    except json.JSONDecodeError as e:
        print(f"[LLM] ❌ JSON parsing FAILED: {str(e)}")
        print(f"[LLM] Error at position: {e.pos}")
        print(f"[LLM] Returning error object")
        print("========== LLM.PY: normalize_invoice() FAILED ==========\n")
        return {"error": "Failed to parse PDF JSON", "items": [], "total": 0}

# --- EXCEL FUNCTION (Enhanced for multiple formats) ---
def extract_bulk_invoices(csv_text: str) -> dict:
    print("\n========== LLM.PY: extract_bulk_invoices() STARTED ==========")
    print(f"[LLM-EXCEL] CSV text length: {len(csv_text)} characters")
    print(f"[LLM-EXCEL] CSV preview (first 500 chars):\n{csv_text[:500]}")
    
    prompt = f"""
    You are a Data Processor converting CSV/Excel data into JSON.
    
    INPUT DATA:
    {csv_text}

    RULES:
    1. Identify the invoice grouping column: usually "Serial Number" or "Invoice Number"
    2. GROUP rows by this invoice identifier
    3. Extract customer from "Party Name" or "Party Company Name"
    4. For EACH GROUP, determine if it has product details:
       
       CASE A - HAS PRODUCT DETAILS (columns like "Product Name", "Qty", "Price"):
       - Extract each product as a separate item
       - 'unit_price' = "Unit Price" or "Price with Tax" / (1 + Tax%/100)
       - 'tax' = Calculate from Tax% if given, or from difference
       - 'qty' = "Qty" column
       - 'total' = "Item Total Amount" or "Price with Tax"
       
       CASE B - NO PRODUCT DETAILS (only "Net Amount", "Total Amount"):
       - Create ONE item called "Invoice Balance"
       - qty = 1
       - unit_price = Net Amount (or Total Amount - Tax Amount)
       - tax = Tax Amount
       - total = Total Amount

    OUTPUT SCHEMA:
    {{
      "invoices": [
        {{
          "invoice_id": string,
          "date": string,
          "customer": {{ "name": string, "phone": string|null }},
          "items": [ 
            {{ 
              "name": string, 
              "qty": number, 
              "unit_price": number, 
              "tax": number, 
              "total": number 
            }} 
          ],
          "subtotal": number,
          "tax_total": number,
          "total": number
        }}
      ]
    }}
    
    IMPORTANT: 
    - If phone is like "999999999.0", convert to "9999999999" (remove .0)
    - Date format: keep as provided (e.g., "12 Nov 2024")
    - Ensure subtotal + tax_total = total
    """
    
    print("[LLM-EXCEL] Sending prompt to Gemini API...")
    print(f"[LLM-EXCEL] Prompt length: {len(prompt)} characters")
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    print("[LLM-EXCEL] Received response from Gemini")
    text = response.text.strip()
    print(f"[LLM-EXCEL] Response text length: {len(text)} characters")
    print(f"[LLM-EXCEL] Raw response preview (first 500 chars):\n{text[:500]}")
    
    match = re.search(r"\{.*\}", text, re.DOTALL)
    clean_text = match.group(0) if match else text
    print(f"[LLM-EXCEL] JSON extraction {'successful' if match else 'FAILED - using raw text'}")

    try:
        result = json.loads(clean_text)
        print("[LLM-EXCEL] ✅ JSON parsing SUCCESSFUL")
        print(f"[LLM-EXCEL] Number of invoices: {len(result.get('invoices', []))}")
        for i, inv in enumerate(result.get('invoices', [])):
            print(f"[LLM-EXCEL] Invoice {i+1}:")
            print(f"  - ID: {inv.get('invoice_id')}")
            print(f"  - Date: {inv.get('date')}")
            print(f"  - Customer: {inv.get('customer', {}).get('name')}")
            print(f"  - Items count: {len(inv.get('items', []))}")
            print(f"  - Total: {inv.get('total')}")
        print(f"[LLM-EXCEL] Full result:\n{json.dumps(result, indent=2)}")
        print("========== LLM.PY: extract_bulk_invoices() COMPLETED ==========\n")
        return result
    except json.JSONDecodeError as e:
        print(f"[LLM-EXCEL] ❌ JSON parsing FAILED: {str(e)}")
        print(f"[LLM-EXCEL] Error at position: {e.pos}")
        print(f"[LLM-EXCEL] Returning empty invoices array")
        print("========== LLM.PY: extract_bulk_invoices() FAILED ==========\n")
        return {"invoices": []}
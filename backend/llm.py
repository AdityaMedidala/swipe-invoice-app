import os
import json
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Using gemini-2.0-flash for speed and accuracy
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def normalize_invoice(raw_text: str, entities: list) -> dict:
    """Extract structured invoice data from OCR text using LLM"""
    
    # Safely format entities for the prompt
    entities_str = json.dumps(entities, indent=2) if entities else "[]"

    prompt = f"""
    You are an expert financial data extractor.
    
    CRITICAL GOAL: Extract a valid JSON object.
    
    INSTRUCTIONS FOR ITEMS:
    1. Extract all products from the item table.
    2. 'unit_price' = Rate/Item column value (price per unit before tax).
    3. 'tax' = GST/Tax column value. Extract ONLY the tax amount number.
       Examples: 
       - "238.10 (5%)" -> tax = 238.10
       - "18%" with Amount 90169.49 and Taxable 90169.49 -> calculate: tax = 0
       - CGST 9.0% 8115.25 -> tax = 8115.25
    4. 'total' = Amount/Final column (the rightmost price column for each item).
    5. 'qty' = Quantity column value (default to 1 if missing).
    6. Include "Making charges", "debit card charges", "Shipping Charges" as separate items with qty=1.
    
    CRITICAL TAX RULES:
    - If tax is shown PER ITEM in the table (like "238.10 (5%)"), extract it for that item.
    - If tax is shown only as INVOICE TOTALS (CGST/SGST/IGST at bottom), set item tax = 0.
    - For Making/Shipping charges with no tax info, set tax = 0.
    - Always capture "tax_total" from the CGST+SGST or IGST total at invoice level.
    
    INSTRUCTIONS FOR EXTRAS (MISSING IN YOUR PREVIOUS CODE):
    1. "total_in_words": Look for "Amount in words", "Rupees", "Total (in words)". Extract the full string.
    2. "bank": Look for "Bank Details", "Account No", "IFSC", "Beneficiary". Extract details.

    SCHEMA:
    {{
      "invoice_id": string,
      "date": string,
      "total_in_words": string|null,
      "customer": {{
        "name": string|null,
        "phone": string|null
      }},
      "bank": {{
        "bank_name": string|null,
        "account_number": string|null,
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
    {entities_str}
    """

    # Using gemini-2.0-flash (Updated from 2.5 which might not be available yet)
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    text = response.text.strip()
    
    # Extract JSON from response
    match = re.search(r"\{.*\}", text, re.DOTALL)
    clean_text = match.group(0) if match else text

    try:
        result = json.loads(clean_text)
        # Handle case where LLM wraps result in "invoices" array for single PDF
        if "invoices" in result and isinstance(result["invoices"], list):
            return result["invoices"][0]
        return result
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {str(e)}")
        # Return a safe fallback structure
        return {
            "error": "Failed to parse PDF JSON", 
            "items": [], 
            "total": 0,
            "bank": {},
            "customer": {}
        }


def extract_bulk_invoices(csv_text: str) -> dict:
    """Extract multiple invoices from CSV/Excel data using LLM"""
    
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
    
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    text = response.text.strip()
    
    # Extract JSON from response
    match = re.search(r"\{.*\}", text, re.DOTALL)
    clean_text = match.group(0) if match else text

    try:
        result = json.loads(clean_text)
        return result
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {str(e)}")
        return {"invoices": []}
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("InvoiceValidator")

def validate_invoice(data: dict) -> dict:
    """
    Validates invoice data, handling key mismatches (qty vs quantity)
    and calculating missing totals.
    """
    # 1. Standardize Items
    items = data.get("items", [])
    clean_items = []
    
    calc_subtotal = 0.0
    calc_tax_total = 0.0

    print(f"[VALIDATOR] Processing {len(items)} items...")

    for i, item in enumerate(items):
        name = item.get("name", "").strip()
        if not name: 
            continue
            
        # --- FIX: Check both 'quantity' and 'qty' ---
        raw_qty = item.get("quantity") or item.get("qty") or 0
        try:
            qty = float(raw_qty)
            # Only default to 1.0 if it's actually 0 (and not just missing)
            if qty <= 0: 
                qty = 1.0 
        except:
            qty = 1.0

        # Extract Price & Tax
        try:
            unit_price = float(item.get("unit_price", 0))
        except:
            unit_price = 0.0

        try:
            tax = float(item.get("tax", 0))
        except:
            tax = 0.0
        
        # Calculate Line Totals
        amount = qty * unit_price
        price_with_tax = amount + tax
        
        calc_subtotal += amount
        calc_tax_total += tax
        
        # Create Clean Item Dictionary
        clean_items.append({
            "name": name,
            "quantity": qty,           # Standardized key
            "unit_price": unit_price,
            "tax": tax,
            "amount": amount,
            "price_with_tax": price_with_tax
        })

    # 2. Update Invoice Totals
    data["items"] = clean_items
    data["subtotal"] = round(calc_subtotal, 2)
    data["tax_total"] = round(calc_tax_total, 2)
    
    # 3. Handle Grand Total
    extracted_total = float(data.get("total", 0))
    
    if extracted_total <= 0:
        data["total"] = round(calc_subtotal + calc_tax_total, 2)
        variance = 0.0
    else:
        variance = abs(extracted_total - (calc_subtotal + calc_tax_total))
        
    # Mark consistent if math checks out (within small margin)
    data["is_consistent"] = variance < 5.0

    # ==================================================
    # 4. PRESERVE EXTRA FIELDS (MISSING IN YOUR CODE)
    # ==================================================
    # Ensure these fields are passed through, or set to null if missing
    data["total_in_words"] = data.get("total_in_words")
    
    # Ensure bank is a dictionary, even if empty
    data["bank"] = data.get("bank") or {
        "bank_name": None,
        "account_number": None,
        "ifsc": None,
        "branch": None
    }

    # 5. Check for Missing Fields
    missing = []
    
    # Check basic fields
    if not data.get("invoice_id") or str(data.get("invoice_id")).lower() in ["unknown", "null", "none", ""]:
        missing.append("invoiceId")
        
    if not data.get("date") or str(data.get("date")).lower() in ["unknown", "null", "none", ""]:
        missing.append("date")
        
    if not data.get("customer", {}).get("name"):
        missing.append("customerName")
        
    if not clean_items:
        missing.append("items")
        
    data["missing_fields"] = missing
    
    return data
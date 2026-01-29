import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("InvoiceValidator")

def validate_invoice(data: dict) -> dict:
    print("\n========== VALIDATOR.PY: validate_invoice() STARTED ==========")
    print(f"[VALIDATOR] Input data keys: {list(data.keys())}")
    
    items = data.get("items", [])
    print(f"[VALIDATOR] Number of items to validate: {len(items)}")
    
    clean_items = []
    
    calc_subtotal = 0.0
    calc_tax_total = 0.0

    logger.info(f"--- Validating Invoice {data.get('invoice_id', 'Unknown')} ---")
    print(f"[VALIDATOR] Invoice ID: {data.get('invoice_id', 'Unknown')}")

    # First pass: collect items and calculate totals
    print(f"\n[VALIDATOR] FIRST PASS: Collecting items and calculating totals...")
    for i, item in enumerate(items):
        name = item.get("name", "").strip()
        
        # Skip items with no name
        if not name:
            logger.warning(f"Item {i}: Missing name, skipping...")
            continue
            
        qty = float(item.get("quantity", 0))
        unit_price = float(item.get("unit_price", 0))
        tax = float(item.get("tax", 0))
        
        # Calculate line totals
        amount = qty * unit_price
        
        calc_subtotal += amount
        calc_tax_total += tax
        
        # Build clean item
        clean_item = {
            "name": name,
            "quantity": qty,
            "unit_price": unit_price,
            "tax": tax,
            "amount": amount,
            "price_with_tax": amount + tax
        }
        clean_items.append(clean_item)

    # Update data with cleaned items and calculated totals
    data["items"] = clean_items
    data["subtotal"] = round(calc_subtotal, 2)
    data["tax_total"] = round(calc_tax_total, 2)
    
    # Recalculate grand total
    calc_grand_total = calc_subtotal + calc_tax_total
    
    # Check consistency
    extracted_total = float(data.get("total", 0))
    variance = abs(extracted_total - calc_grand_total)
    
    print(f"[VALIDATOR] Calculated Grand Total: {calc_grand_total}")
    print(f"[VALIDATOR] Extracted Total: {extracted_total}")
    print(f"[VALIDATOR] Variance: {variance}")
    
    # Mark as consistent if variance is small (< 1.0)
    data["is_consistent"] = variance < 1.0

    # ---------------------------------------------------------
    # CHECK FOR MISSING FIELDS (UPDATED LOGIC)
    # ---------------------------------------------------------
    missing = []
    invalid_values = ["unknown", "null", "none", "", "n/a"]

    # 1. Validate Date
    date_val = data.get("date")
    if not date_val or str(date_val).strip().lower() in invalid_values:
        missing.append("date")
        print(f"[VALIDATOR] Missing: date (Value: '{date_val}')")
        
    # 2. Validate Customer Name
    cust_name = data.get("customer", {}).get("name")
    if not cust_name or str(cust_name).strip().lower() in invalid_values:
        missing.append("customerName")
        print(f"[VALIDATOR] Missing: customerName (Value: '{cust_name}')")
        
    # 3. Validate Items
    if not clean_items:
        missing.append("items")
        print(f"[VALIDATOR] Missing: items (No valid items found)")
        
    # 4. Validate Total Amount
    # Check if total is missing OR zero/negative
    if extracted_total <= 0:
        missing.append("totalAmount")
        print(f"[VALIDATOR] Missing: totalAmount (Value: {extracted_total})")
        
    # 5. Validate Invoice ID
    inv_id = data.get("invoice_id")
    if not inv_id or str(inv_id).strip().lower() in invalid_values:
        missing.append("invoiceId")
        print(f"[VALIDATOR] Missing: invoiceId (Value: '{inv_id}')")
        
    data["missing_fields"] = missing
    print(f"[VALIDATOR] Total missing fields: {len(missing)}")
    print(f"[VALIDATOR] Missing fields list: {missing}")

    print(f"\n[VALIDATOR] Final validated data summary:")
    print(f"  - invoice_id: {data.get('invoice_id')}")
    print(f"  - status: {'Consistent' if data['is_consistent'] else 'Inconsistent'}")
    print(f"  - missing: {missing}")
    print("========== VALIDATOR.PY: validate_invoice() COMPLETED ==========\n")
    
    return data
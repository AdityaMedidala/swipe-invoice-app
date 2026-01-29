import re
from typing import List, Dict
from models import CanonicalInvoice, InvoiceItem, Customer, BankDetails


# ---------------- HELPERS ----------------

def _all(entities, t):
    return [e for e in entities if e.get("type_") == t]


def _one(entities, t):
    for e in entities:
        if e.get("type_") == t:
            return e
    return None


def _val(e):
    if not e:
        return None
    nv = e.get("normalized_value")
    if nv:
        if "float_value" in nv:
            return float(nv["float_value"])
        if "text" in nv:
            return nv["text"]
    return e.get("mention_text")


# ---------------- OCR TOTAL ----------------

def extract_total_from_text(text: str):
    matches = re.findall(
        r"(?:Total Amount|Total|Amount Due).*?(\d{1,3}(?:,\d{3})*\.\d{2})",
        text,
        re.IGNORECASE
    )
    if matches:
        return float(matches[-1].replace(",", ""))
    return 0.0


# ---------------- OCR TAX ----------------

def extract_tax_from_text(text: str):
    tax_lines = re.findall(
        r"(CGST|SGST|IGST).*?(\d{1,3}(?:,\d{3})*\.\d{2})",
        text
    )
    return sum(float(v.replace(",", "")) for _, v in tax_lines)


# ---------------- OCR BANK ----------------

def extract_bank_from_text(text: str):
    def g(p):
        m = re.search(p, text, re.IGNORECASE)
        return m.group(1).strip() if m else None

    return {
        "bankName": g(r"Bank:\s*(.+)"),
        "accountNumber": g(r"Account\s*#:\s*(\d+)"),
        "ifsc": g(r"IFSC\s*(?:Code)?:\s*(\w+)"),
        "branch": g(r"Branch:\s*(.+)")
    }


# ---------------- OCR WORDS ----------------

def extract_words(text):
    m = re.search(
        r"Total amount.*?:\s*(.+)",
        text,
        re.IGNORECASE
    )
    return m.group(1).strip() if m else None


# ---------------- OCR TABLE EXTRACTOR ----------------

def extract_items_from_text(text: str):
    """
    Fallback logic: Manually parses rows from raw text when DocAI 
    fails to extract the full table.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    start = -1
    end = -1

    # 1. Find table header
    for i, line in enumerate(lines):
        if "Description" in line and "Quantity" in line:
            start = i + 1
            break

    if start == -1:
        return []

    # 2. Find table end
    for i in range(start, len(lines)):
        if "Total Items" in lines[i] or "Sub Total" in lines[i]:
            end = i
            break

    if end == -1:
        end = len(lines)

    rows = lines[start:end]
    items = []

    for r in rows:
        # Regex to capture: Name (words), Rate (num), Qty (num), Total (num)
        # Handles commas in numbers
        m = re.match(
            r"(.*?)\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)$",
            r
        )

        if not m:
            continue

        name = m.group(1).strip()
        rate = float(m.group(2).replace(",", ""))
        qty = float(m.group(3).replace(",", ""))
        amt = float(m.group(4).replace(",", ""))

        items.append(
            InvoiceItem(
                itemName=name,
                quantity=qty,
                unitPrice=rate,
                amount=amt,
                taxAmount=0, # OCR fallback usually sums tax separately
                taxRate=0
            )
        )

    return items


# ---------------- MAIN ----------------

def map_entities_to_invoice(entities: List[Dict], text: str):

    # -------- CUSTOMER --------
    name = _val(_one(entities, "receiver_name"))
    phone = _val(_one(entities, "receiver_phone"))

    # -------- HEADER --------
    invoice_id = _val(_one(entities, "invoice_id"))
    date = _val(_one(entities, "invoice_date"))

    # -------- ITEMS --------
    items = []

    # Strategy A: Extract from Document AI Entities
    for li in _all(entities, "line_item"):
        props = li.get("properties", [])

        def p(t):
            for x in props:
                if x["type_"] == t:
                    return _val(x)
            return None

        name_i = p("line_item/description") or ""

        # Skip non-product lines (like subtotal rows tagged as line items)
        if re.search(r"charge|fee|shipping|debit|making|round", name_i, re.IGNORECASE):
            continue

        item = InvoiceItem(
            itemName=name_i.strip() or "Unknown",
            quantity=float(p("line_item/quantity") or 1),
            unitPrice=float(p("line_item/unit_price") or 0),
            taxRate=float(p("line_item/tax_rate") or 0),
            taxAmount=float(p("line_item/tax_amount") or 0),
            amount=float(p("line_item/amount") or 0),
            discount=p("line_item/discount")
        )

        if item.amount > 0:
            items.append(item)

    # Strategy B: Fallback to OCR Table Reconstruction
    # If DocAI returns significantly fewer items than expected or 0 items
    if len(items) < 2: 
        text_items = extract_items_from_text(text)
        # Only switch if the OCR parser actually found more data
        if len(text_items) > len(items):
            items = text_items

    # -------- TOTAL --------
    entity_total = _val(_one(entities, "total_amount")) or 0
    net_amount = _val(_one(entities, "net_amount")) or 0
    text_total = extract_total_from_text(text)

    # In Indian invoices, the OCR text total is often the most reliable 
    # when the structural parser gets confused by GST tables.
    total = max(entity_total, net_amount, text_total)

    # -------- TAX --------
    tax = extract_tax_from_text(text)

    # -------- BANK --------
    bank = BankDetails(**extract_bank_from_text(text))

    # -------- WORDS --------
    words = extract_words(text)

    # -------- MISSING --------
    missing = []
    if not name: missing.append("customer.name")
    if not phone: missing.append("customer.phone")
    if not items: missing.append("items")

    # -------- BUILD --------
    return CanonicalInvoice(
        serialNumber=invoice_id,
        date=date,
        customer=Customer(
            name=name,
            phone=phone
        ),
        totalAmount=round(total, 2),
        taxAmount=round(tax, 2),
        totalInWords=words,
        bankDetails=bank,
        items=items,
        missingFields=missing
    )
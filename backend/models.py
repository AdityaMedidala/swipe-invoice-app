from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


# ----------------------------
# Item Model
# ----------------------------

class InvoiceItem(BaseModel):
    itemName: str = Field(..., description="Name of the product/service")

    quantity: float = Field(
        default=1.0,
        description="Quantity purchased"
    )

    unitPrice: float = Field(
        default=0.0,
        description="Base price per unit (before tax/discount)"
    )

    taxRate: Optional[float] = Field(
        default=None,
        description="Tax percentage (e.g. 18 for 18%)"
    )

    taxAmount: float = Field(
        default=0.0,
        description="Tax amount for this item"
    )

    discount: Optional[float] = Field(
        default=None,
        description="Discount applied on this item (absolute value)"
    )

    amount: float = Field(
        default=0.0,
        description="Final amount including tax and discount"
    )


# ----------------------------
# Customer Model
# ----------------------------

class Customer(BaseModel):
    name: Optional[str] = Field(
        default=None,
        description="Customer name"
    )

    phone: Optional[str] = Field(
        default=None,
        description="Customer phone number"
    )


# ----------------------------
# Bank Details Model
# ----------------------------

class BankDetails(BaseModel):
    bankName: Optional[str] = None
    accountNumber: Optional[str] = None
    ifsc: Optional[str] = None
    branch: Optional[str] = None


# ----------------------------
# Main Invoice Model
# ----------------------------

class CanonicalInvoice(BaseModel):

    # System ID (internal)
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Internal unique invoice ID"
    )

    # Invoice metadata
    serialNumber: Optional[str] = None
    date: Optional[str] = None  # Keep string (YYYY-MM-DD) for frontend

    # Customer info
    customer: Customer = Field(default_factory=Customer)

    # Financials
    totalAmount: float = 0.0
    taxAmount: float = 0.0

    totalInWords: Optional[str] = None

    # Bank info
    bankDetails: BankDetails = Field(default_factory=BankDetails)

    # Items
    items: List[InvoiceItem] = Field(default_factory=list)

    # Validation / UI helpers
    missingFields: List[str] = Field(
        default_factory=list,
        description="List of missing or unreliable fields"
    )


# ----------------------------
# API Response Wrapper
# ----------------------------

class InvoiceResponse(BaseModel):
    invoice: CanonicalInvoice

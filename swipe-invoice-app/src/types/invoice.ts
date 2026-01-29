//Normalized customers and products for redux selectors
// Invoice items are embedded to simplify tables
export interface Customer {
  id: string;
  name: string | null;
  phone: string | null;
  address?: string | null;
  totalPurchaseAmount: number;
}

export interface Product {
  id: string;
  name: string | null;

  unitPrice: number | null;
  tax: number | null;
  priceWithTax: number | null;

  totalQuantity: number;
}

export interface InvoiceItem {
  id: string;
  invoiceId: string;
  productId: string;

  itemName: string | null;
  quantity: number | null;
  unitPrice: number | null;
  tax: number | null;
  amount: number | null;
}

export interface AdditionalCharge {
  label: string;
  amount: number;
}

export interface Invoice {
  id: string;  
  serialNumber: string | null;
  date: string | null;
  status: 'Pending' | 'Paid' | 'Overdue' | null;
  totalAmount: number | null;
  taxAmount: number | null;
  taxType: 'IGST' | 'CGST_SGST' | null;
  customerId: string | null;
  customerName: string | null;
  customerPhone:string | null;
  items: InvoiceItem[];
  additionalCharges?: AdditionalCharge[];

  //In case Ai failes but option ?
  rawText?: string;
}

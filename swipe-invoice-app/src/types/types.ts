export interface BankDetails {
  bankName: string | null;
  accountNumber: string | null;
  ifsc: string | null;
  branch: string | null;
}

export interface InvoiceItem {
  productId: string;
  itemName: string;
  quantity: number;
  unitPrice: number;
  taxAmount: number;
  amount: number;
}

export interface Invoice {
  invoiceId: string;
  serialNumber: string;
  date: string;
  customerName: string;
  customerPhone: string | null;
  customerId?: string | null;
  totalAmount: number;
  taxAmount: number;
  totalInWords: string | null;
  bankDetails: BankDetails | null;
  items: InvoiceItem[];
  isConsistent: boolean;
  missingFields: string[];
}

export interface Product {
  id: string;
  name: string;
  unitPrice: number;
  tax: number;
  priceWithTax: number;
  quantity?: number;
}

export interface Customer {
  id: string;
  name: string;
  phone: string | null;
  totalPurchaseAmount: number;
}
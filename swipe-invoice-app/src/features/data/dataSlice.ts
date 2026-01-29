import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { Invoice, Customer, Product } from '../../types/types';

interface DataState {
  invoices: Invoice[];
  customers: Customer[];
  products: Product[];
}

const initialState: DataState = {
  invoices: [],
  customers: [],
  products: [],
};

const dataSlice = createSlice({
  name: 'data',
  initialState,
  reducers: {
    addInvoice: (state, action: PayloadAction<any>) => {
      const raw = action.payload.invoice || action.payload;

      // Build invoice from raw data
      const inv: Invoice = {
        invoiceId: raw.invoiceId || raw.invoice_id || "",
        serialNumber: raw.serialNumber || raw.invoice_id || "",
        date: raw.date || "",
        customerName: raw.customerName || raw.customer?.name || "Unknown",
        customerPhone: raw.customerPhone || raw.customer?.phone || null,
        totalAmount: raw.totalAmount || raw.total || 0,
        taxAmount: raw.taxAmount || raw.tax_total || 0,
        totalInWords: raw.totalInWords || raw.total_in_words || null,
        bankDetails: raw.bankDetails || raw.bank || null,
        isConsistent: raw.isConsistent !== undefined ? raw.isConsistent : true,
        missingFields: raw.missingFields || [],
        items: (raw.items || []).map((i: any) => ({
          productId: i.productId || `prod-${Date.now()}-${Math.random()}`,
          itemName: i.itemName || i.name || i.description || "Unknown",
          quantity: i.quantity || i.qty || 1,
          unitPrice: i.unitPrice || i.unit_price || 0,
          taxAmount: i.taxAmount || i.tax || 0,
          amount: i.amount || i.total || 0
        }))
      };

      state.invoices.push(inv);

      // Process items for Products table
      inv.items.forEach((item) => {
        const name = item.itemName;
        if (!name) return;

        // Skip service charges
        const isService = /shipping|charge|making|fee/i.test(name);
        if (isService) return;

        const existing = state.products.find((p) => p.name === name);
        const price = item.unitPrice || 0;

        if (existing) {
          // Update existing product
          if (price > 0) {
            existing.unitPrice = price;
            existing.tax = item.taxAmount || existing.tax || 0;
            existing.priceWithTax = existing.unitPrice + existing.tax;
          }
          existing.quantity = (existing.quantity || 0) + item.quantity;
        } else {
          // Create new product
          state.products.push({
            id: item.productId || `prod-${Date.now()}-${Math.random()}`,
            name,
            unitPrice: price,
            tax: item.taxAmount || 0,
            priceWithTax: price + (item.taxAmount || 0),
            quantity: item.quantity
          });
        }
      });

      // Process customer
      const cname = inv.customerName;
      if (!cname || cname === "Unknown") return;

      const cust = state.customers.find((c) => c.name === cname);

      if (!cust) {
        // Create new customer
        state.customers.push({
          id: `cust-${Date.now()}-${Math.random()}`,
          name: cname,
          phone: inv.customerPhone || null,
          totalPurchaseAmount: inv.totalAmount
        });
      } else {
        // Update existing customer
        cust.totalPurchaseAmount += inv.totalAmount;
      }
    },

    updateProduct: (state, action) => {
      const { id, updates } = action.payload;
      const index = state.products.findIndex(p => p.id === id);
      if (index === -1) return;

      const old = state.products[index];

      // Normalize numbers
      const unitPrice = updates.unitPrice !== undefined ? Number(updates.unitPrice) : old.unitPrice;
      const tax = updates.tax !== undefined ? Number(updates.tax) : old.tax;
      const name = updates.name ?? old.name;

      // Update product
      state.products[index] = {
        ...old,
        name,
        unitPrice,
        tax,
        priceWithTax: unitPrice + tax,
      };

      // Update all invoice items using this product
      state.invoices.forEach(inv => {
        let invoiceSubtotal = 0;
        let invoiceTax = 0;

        inv.items.forEach(item => {
          if (item.productId === id) {
            item.itemName = name;
            item.unitPrice = unitPrice;
            item.taxAmount = tax;
            item.amount = unitPrice * item.quantity + tax;
          }

          invoiceSubtotal += item.unitPrice * item.quantity;
          invoiceTax += item.taxAmount;
        });

        // Recalculate invoice totals
        const newTotal = invoiceSubtotal + invoiceTax;
        inv.totalAmount = Number(newTotal.toFixed(2));
        inv.taxAmount = Number(invoiceTax.toFixed(2));
        inv.isConsistent = Math.abs(inv.totalAmount - newTotal) <= 1;
      });

      // Recalculate customer totals
      state.customers.forEach(cust => {
        let sum = 0;
        state.invoices.forEach(inv => {
          if (inv.customerName === cust.name) {
            sum += inv.totalAmount;
          }
        });
        cust.totalPurchaseAmount = Number(sum.toFixed(2));
      });
    },

    updateCustomer: (state, action) => {
      const { id, updates } = action.payload;
      const cust = state.customers.find(c => c.id === id);
      
      if (cust) {
        const oldName = cust.name;
        Object.assign(cust, updates);
        
        // Update customer name in all invoices
        if (updates.name && updates.name !== oldName) {
          state.invoices.forEach(inv => {
            if (inv.customerName === oldName) {
              inv.customerName = updates.name;
            }
          });
        }
      }
    },

    updateInvoice: (state, action) => {
      const { id, updates } = action.payload;
      const inv = state.invoices.find(i => i.invoiceId === id);
      
      if (inv) {
        Object.assign(inv, updates);
        
        // Recalculate consistency
        const total = Number(inv.totalAmount) || 0;
        const calcSub = inv.items.reduce((acc, item) => acc + item.amount, 0);
        inv.isConsistent = Math.abs(total - calcSub) <= 1.0;
        
        // Remove from missing fields if now filled
        if (updates.date && inv.missingFields.includes('date')) {
          inv.missingFields = inv.missingFields.filter(f => f !== 'date');
        }
        if (updates.serialNumber && inv.missingFields.includes('invoice_id')) {
          inv.missingFields = inv.missingFields.filter(f => f !== 'invoice_id');
        }
        if (updates.customerName && inv.missingFields.includes('customerName')) {
          inv.missingFields = inv.missingFields.filter(f => f !== 'customerName');
        }
      }
    }
  },
});

export const { addInvoice, updateProduct, updateCustomer, updateInvoice } = dataSlice.actions;
export default dataSlice.reducer;
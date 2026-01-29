import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { Invoice, Customer, Product } from '../../types/types';

console.log('\n========== DATASLICE.TS: Module Loading ==========');

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

console.log('[REDUX] Initial state:', initialState);

const dataSlice = createSlice({
  name: 'data',
  initialState,
  reducers: {
    addInvoice: (state, action: PayloadAction<any>) => {
      console.log('\n========== DATASLICE.TS: addInvoice REDUCER STARTED ==========');
      console.log('[REDUX-ADD] Action received:', action);
      console.log('[REDUX-ADD] Action type:', action.type);
      console.log('[REDUX-ADD] Action payload:', action.payload);
      console.log('[REDUX-ADD] Payload keys:', Object.keys(action.payload || {}));

      const raw = action.payload.invoice || action.payload;
      console.log('[REDUX-ADD] Raw data (after unwrapping):', raw);
      console.log('[REDUX-ADD] Raw data keys:', Object.keys(raw || {}));

      console.log('\n[REDUX-ADD] Building Invoice object...');
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
        items: (raw.items || []).map((i: any, idx: number) => {
          console.log(`[REDUX-ADD] Processing item ${idx + 1}:`, i);
          const item = {
            productId: i.productId || `prod-${Date.now()}-${Math.random()}`,
            itemName: i.itemName || i.name || i.description || "Unknown",
            quantity: i.quantity || i.qty || 1,
            unitPrice: i.unitPrice || i.unit_price || 0,
            taxAmount: i.taxAmount || i.tax || 0,
            amount: i.amount || i.total || 0
          };
          console.log(`[REDUX-ADD] Mapped item ${idx + 1}:`, item);
          return item;
        })
      };

      console.log('\n[REDUX-ADD] Final Invoice object:');
      console.log('  - invoiceId:', inv.invoiceId);
      console.log('  - serialNumber:', inv.serialNumber);
      console.log('  - date:', inv.date);
      console.log('  - customerName:', inv.customerName);
      console.log('  - customerPhone:', inv.customerPhone);
      console.log('  - totalAmount:', inv.totalAmount);
      console.log('  - taxAmount:', inv.taxAmount);
      console.log('  - isConsistent:', inv.isConsistent);
      console.log('  - missingFields:', inv.missingFields);
      console.log('  - items count:', inv.items.length);
      console.log('[REDUX-ADD] Full invoice object:', inv);

      console.log('\n[REDUX-ADD] Current invoices count before push:', state.invoices.length);
      state.invoices.push(inv);
      console.log('[REDUX-ADD] ✅ Invoice pushed to state');
      console.log('[REDUX-ADD] New invoices count:', state.invoices.length);

      console.log('\n[REDUX-ADD] Processing items for Products table...');
      inv.items.forEach((item, idx) => {
        console.log(`\n[REDUX-ADD] Processing item ${idx + 1}/${inv.items.length}: ${item.itemName}`);
        
        const name = item.itemName;
        if (!name) {
          console.log(`[REDUX-ADD] ⚠️ Item ${idx + 1} has no name, skipping`);
          return;
        }

        const isService = /shipping|charge|making|fee/i.test(name);
        console.log(`[REDUX-ADD] Is service charge: ${isService}`);
        
        if (isService) {
          console.log(`[REDUX-ADD] Skipping service charge: ${name}`);
          return;
        }

        console.log(`[REDUX-ADD] Checking if product "${name}" already exists...`);
        const existing = state.products.find((p) => p.name === name);
        console.log(`[REDUX-ADD] Existing product found: ${!!existing}`);
        
        const price = item.unitPrice || 0;
        console.log(`[REDUX-ADD] Item unit price: ${price}`);

        if (existing) {
          console.log(`[REDUX-ADD] Updating existing product: ${name}`);
          console.log(`[REDUX-ADD] Old values:`, {
            unitPrice: existing.unitPrice,
            tax: existing.tax,
            priceWithTax: existing.priceWithTax,
            quantity: existing.quantity
          });
          
          if (price > 0) {
            existing.unitPrice = price;
            // 🟢 FIX 1: Update tax for existing products too if available
            existing.tax = item.taxAmount || existing.tax || 0;
            existing.priceWithTax = existing.unitPrice + existing.tax;
            console.log(`[REDUX-ADD] Updated price and tax`);
          }
          existing.quantity = (existing.quantity || 0) + item.quantity;
          
          console.log(`[REDUX-ADD] New values:`, {
            unitPrice: existing.unitPrice,
            tax: existing.tax,
            priceWithTax: existing.priceWithTax,
            quantity: existing.quantity
          });
        } else {
          console.log(`[REDUX-ADD] Creating new product: ${name}`);
          const newProduct = {
            id: item.productId || `prod-${Date.now()}-${Math.random()}`,
            name,
            unitPrice: price,
            // 🟢 FIX 2: Use the extracted tax instead of 0
            tax: item.taxAmount || 0,
            priceWithTax: price + (item.taxAmount || 0),
            quantity: item.quantity
          };
          console.log(`[REDUX-ADD] New product object:`, newProduct);
          state.products.push(newProduct);
          console.log(`[REDUX-ADD] ✅ Product added to state`);
        }
      });

      console.log(`[REDUX-ADD] Products processing complete. Total products: ${state.products.length}`);

      console.log('\n[REDUX-ADD] Processing Customer...');
      const cname = inv.customerName;
      console.log(`[REDUX-ADD] Customer name: ${cname}`);
      
      if (!cname || cname === "Unknown") {
        console.log(`[REDUX-ADD] ⚠️ Invalid customer name, skipping customer processing`);
        console.log('========== DATASLICE.TS: addInvoice REDUCER COMPLETED ==========\n');
        return;
      }

      console.log(`[REDUX-ADD] Checking if customer "${cname}" already exists...`);
      const cust = state.customers.find((c) => c.name === cname);
      console.log(`[REDUX-ADD] Existing customer found: ${!!cust}`);

      if (!cust) {
        console.log(`[REDUX-ADD] Creating new customer: ${cname}`);
        const newCustomer = {
          id: `cust-${Date.now()}-${Math.random()}`,
          name: cname,
          phone: inv.customerPhone || null,
          totalPurchaseAmount: inv.totalAmount
        };
        console.log(`[REDUX-ADD] New customer object:`, newCustomer);
        state.customers.push(newCustomer);
        console.log(`[REDUX-ADD] ✅ Customer added to state`);
      } else {
        console.log(`[REDUX-ADD] Updating existing customer: ${cname}`);
        console.log(`[REDUX-ADD] Old totalPurchaseAmount: ${cust.totalPurchaseAmount}`);
        cust.totalPurchaseAmount += inv.totalAmount;
        console.log(`[REDUX-ADD] New totalPurchaseAmount: ${cust.totalPurchaseAmount}`);
      }

      console.log(`[REDUX-ADD] Customer processing complete. Total customers: ${state.customers.length}`);
      console.log('\n[REDUX-ADD] Final state snapshot:');
      console.log('  - Invoices:', state.invoices.length);
      console.log('  - Products:', state.products.length);
      console.log('  - Customers:', state.customers.length);
      console.log('========== DATASLICE.TS: addInvoice REDUCER COMPLETED ==========\n');
    },

    updateProduct: (state, action) => {
  const { id, updates } = action.payload;

  // 1. Find product
  const index = state.products.findIndex(p => p.id === id);

  if (index === -1) return;

  const old = state.products[index];

  // 2. Normalize numbers
  const unitPrice =
    updates.unitPrice !== undefined
      ? Number(updates.unitPrice)
      : old.unitPrice;

  const tax =
    updates.tax !== undefined
      ? Number(updates.tax)
      : old.tax;

  const name = updates.name ?? old.name;

  // 3. Update product (replace object)
  const updatedProduct: Product = {
    ...old,
    name,
    unitPrice,
    tax,
    priceWithTax: unitPrice + tax,
  };

  state.products[index] = updatedProduct;

  // 4. Update ALL invoice items that use this product
  state.invoices.forEach(inv => {

    let invoiceSubtotal = 0;
    let invoiceTax = 0;

    inv.items.forEach(item => {

      if (item.productId === id) {

        // Update item fields
        item.itemName = name;
        item.unitPrice = unitPrice;
        item.taxAmount = tax;

        // Recalculate amount
        item.amount =
          unitPrice * item.quantity + tax;
      }

      invoiceSubtotal += item.unitPrice * item.quantity;
      invoiceTax += item.taxAmount;
    });

    // 5. Recalculate invoice totals
    const newTotal = invoiceSubtotal + invoiceTax;

    inv.totalAmount = Number(newTotal.toFixed(2));
    inv.taxAmount = Number(invoiceTax.toFixed(2));

    // 6. Re-run consistency check
    inv.isConsistent =
      Math.abs(inv.totalAmount - newTotal) <= 1;
  });

  // 7. Recalculate customer totals
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
      console.log('\n========== DATASLICE.TS: updateCustomer REDUCER STARTED ==========');
      console.log('[REDUX-UPDATE-CUST] Action:', action);
      
      const { id, updates } = action.payload;
      console.log('[REDUX-UPDATE-CUST] Customer ID:', id);
      console.log('[REDUX-UPDATE-CUST] Updates:', updates);

      console.log('[REDUX-UPDATE-CUST] Finding customer with ID:', id);
      const cust = state.customers.find(c => c.id === id);
      console.log('[REDUX-UPDATE-CUST] Customer found:', !!cust);
      
      if (cust) {
        const oldName = cust.name;
        console.log('[REDUX-UPDATE-CUST] Old customer name:', oldName);
        console.log('[REDUX-UPDATE-CUST] Old customer:', cust);
        
        Object.assign(cust, updates);
        console.log('[REDUX-UPDATE-CUST] Updated customer:', cust);
        
        // REQ 3: Ensure changes in Customers tab reflect in Invoices tab
        if (updates.name && updates.name !== oldName) {
          console.log('[REDUX-UPDATE-CUST] Customer name changed, updating invoices...');
          let updatedCount = 0;
          
          state.invoices.forEach(inv => {
            if (inv.customerName === oldName) {
              console.log(`[REDUX-UPDATE-CUST] Updating invoice ${inv.invoiceId} customer name`);
              inv.customerName = updates.name;
              updatedCount++;
            }
          });
          
          console.log(`[REDUX-UPDATE-CUST] Updated ${updatedCount} invoice(s)`);
        }
        
        console.log('[REDUX-UPDATE-CUST] ✅ Customer updated');
      } else {
        console.log('[REDUX-UPDATE-CUST] ❌ Customer not found');
      }
      
      console.log('========== DATASLICE.TS: updateCustomer REDUCER COMPLETED ==========\n');
    },

    updateInvoice: (state, action) => {
      console.log('\n========== DATASLICE.TS: updateInvoice REDUCER STARTED ==========');
      console.log('[REDUX-UPDATE-INV] Action:', action);
      
      const { id, updates } = action.payload;
      console.log('[REDUX-UPDATE-INV] Invoice ID:', id);
      console.log('[REDUX-UPDATE-INV] Updates:', updates);

      console.log('[REDUX-UPDATE-INV] Finding invoice with ID:', id);
      const inv = state.invoices.find(i => i.invoiceId === id);
      console.log('[REDUX-UPDATE-INV] Invoice found:', !!inv);
      
      if (inv) {
        console.log('[REDUX-UPDATE-INV] Old invoice:', inv);
        Object.assign(inv, updates);
        console.log('[REDUX-UPDATE-INV] Updated invoice:', inv);
        
        console.log('[REDUX-UPDATE-INV] Recalculating consistency...');
        const total = Number(inv.totalAmount) || 0;
        const calcSub = inv.items.reduce((acc, item) => acc + item.amount, 0);
        console.log('[REDUX-UPDATE-INV] Total amount:', total);
        console.log('[REDUX-UPDATE-INV] Calculated sum of items:', calcSub);
        console.log('[REDUX-UPDATE-INV] Difference:', Math.abs(total - calcSub));
        
        inv.isConsistent = Math.abs(total - calcSub) <= 1.0;
        console.log('[REDUX-UPDATE-INV] isConsistent:', inv.isConsistent);
        
        console.log('[REDUX-UPDATE-INV] Checking missing fields updates...');
        if (updates.date && inv.missingFields.includes('date')) {
          console.log('[REDUX-UPDATE-INV] Removing "date" from missing fields');
          inv.missingFields = inv.missingFields.filter(f => f !== 'date');
        }
        if (updates.serialNumber && inv.missingFields.includes('invoice_id')) {
          console.log('[REDUX-UPDATE-INV] Removing "invoice_id" from missing fields');
          inv.missingFields = inv.missingFields.filter(f => f !== 'invoice_id');
        }
        if (updates.customerName && inv.missingFields.includes('customerName')) {
          console.log('[REDUX-UPDATE-INV] Removing "customerName" from missing fields');
          inv.missingFields = inv.missingFields.filter(f => f !== 'customerName');
        }
        
        console.log('[REDUX-UPDATE-INV] Updated missing fields:', inv.missingFields);
        console.log('[REDUX-UPDATE-INV] ✅ Invoice updated');
      } else {
        console.log('[REDUX-UPDATE-INV] ❌ Invoice not found');
      }
      
      console.log('========== DATASLICE.TS: updateInvoice REDUCER COMPLETED ==========\n');
    }
  },
});

console.log('[REDUX] dataSlice created');
console.log('[REDUX] Available actions:', Object.keys(dataSlice.actions));

export const { addInvoice, updateProduct, updateCustomer, updateInvoice } = dataSlice.actions;

console.log('[REDUX] Actions exported:', { addInvoice, updateProduct, updateCustomer, updateInvoice });
console.log('========== DATASLICE.TS: Module Loaded ==========\n');

export default dataSlice.reducer;
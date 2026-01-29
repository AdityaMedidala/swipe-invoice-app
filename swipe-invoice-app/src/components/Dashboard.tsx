import { useMemo } from 'react';
import { Tabs, Badge, Text, Paper, Group, Grid, Table, Card, Title } from '@mantine/core';
import { MantineReactTable, useMantineReactTable, type MRT_ColumnDef } from 'mantine-react-table';
import { useSelector, useDispatch } from 'react-redux';
import { IconReceipt, IconUsers, IconBox, IconBuildingBank, IconCoinRupee } from '@tabler/icons-react';
import { updateProduct, updateCustomer, updateInvoice } from '../features/data/dataSlice';
import type { Invoice, Product, Customer, InvoiceItem } from '../types/types'

export default function Dashboard() {
  const dispatch = useDispatch();
  const { invoices, products, customers } = useSelector((state: any) => state.data);

  // Highlight empty/invalid cells
  const renderValidatedCell = ({ cell }: any) => {
    const val = cell.getValue();
    const isInvalid = !val || val === "Unknown" || val === "null";
    
    return (
      <Text c={isInvalid ? 'red' : 'inherit'} fw={isInvalid ? 700 : 400}>
        {val || "Required"}
      </Text>
    );
  };

  // Invoice columns
  const invoiceColumns = useMemo<MRT_ColumnDef<Invoice>[]>(() => [
    {
      accessorKey: 'isConsistent',
      header: 'Status',
      size: 90,
      enableEditing: false,
      Cell: ({ row }) => {
        const inv = row.original;
        if (inv.missingFields?.length > 0) return <Badge color="red">Incomplete</Badge>;
        if (!inv.isConsistent) return <Badge color="orange">Mismatch</Badge>;
        return <Badge color="green">OK</Badge>;
      }
    },
    { 
      accessorKey: 'serialNumber', 
      header: 'Invoice #', 
      size: 100,
      enableEditing: true,
      Cell: renderValidatedCell
    },
    { 
      accessorKey: 'date', 
      header: 'Date', 
      size: 100,
      enableEditing: true,
      Cell: renderValidatedCell
    },
    { 
      accessorKey: 'customerName', 
      header: 'Customer',
      enableEditing: true,
      Cell: renderValidatedCell
    },
    { 
      accessorKey: 'totalAmount', 
      header: 'Total Amount',
      Cell: ({ cell }) => <Text fw={700}>₹{cell.getValue<number>()?.toLocaleString()}</Text>
    },
    { 
      accessorKey: 'taxAmount', 
      header: 'Total Tax',
      Cell: ({ cell }) => <Text c="dimmed">₹{cell.getValue<number>()?.toLocaleString()}</Text>
    },
  ], []);

  // Product columns
  const productColumns = useMemo<MRT_ColumnDef<Product>[]>(() => [
    { 
      accessorKey: 'name', 
      header: 'Product Name', 
      enableEditing: true,
      Cell: renderValidatedCell
    },
    { 
      accessorKey: 'quantity', 
      header: 'Quantity',
      enableEditing: false,
      Cell: ({ row }) => row.original.quantity || 0
    },
    { accessorKey: 'unitPrice', header: 'Unit Price', enableEditing: true },
    { accessorKey: 'tax', header: 'Tax', enableEditing: true },
    { 
      accessorKey: 'priceWithTax', 
      header: 'Total Price', 
      enableEditing: false,
      Cell: ({ row }) => {
        const p = row.original;
        const total = (Number(p.unitPrice) || 0) * (Number(p.quantity) || 1) + (Number(p.tax) || 0);
        return `₹${total.toFixed(2)}`;
      }
    },
  ], []);

  // Customer columns
  const customerColumns = useMemo<MRT_ColumnDef<Customer>[]>(() => [
    { 
      accessorKey: 'name', 
      header: 'Name', 
      enableEditing: true,
      Cell: renderValidatedCell
    },
    { 
      accessorKey: 'phone', 
      header: 'Phone', 
      enableEditing: true,
      Cell: renderValidatedCell
    },
    { accessorKey: 'totalPurchaseAmount', header: 'Total Spend', enableEditing: false },
  ], []);

  // Invoice detail panel
  const renderDetailPanel = ({ row }: { row: { original: Invoice } }) => {
    const inv = invoices.find((i: Invoice) => i.invoiceId === row.original.invoiceId) || row.original;
    
    return (
      <Paper p="md" withBorder bg="gray.0">
        <Grid>
          <Grid.Col span={4}>
            <Card shadow="sm" padding="sm" radius="md" withBorder>
              <Group mb="xs">
                <IconBuildingBank size={20} color="blue" />
                <Text fw={700} size="sm">Bank Details</Text>
              </Group>
              <Text size="xs"><b>Bank:</b> {inv.bankDetails?.bankName || 'N/A'}</Text>
              <Text size="xs"><b>Acc #:</b> {inv.bankDetails?.accountNumber || 'N/A'}</Text>
              <Text size="xs"><b>IFSC:</b> {inv.bankDetails?.ifsc || 'N/A'}</Text>
              <Text size="xs"><b>Branch:</b> {inv.bankDetails?.branch || 'N/A'}</Text>
            </Card>
          </Grid.Col>

          <Grid.Col span={8}>
            <Card shadow="sm" padding="sm" radius="md" withBorder h="100%">
              <Group mb="xs">
                <IconCoinRupee size={20} color="green" />
                <Text fw={700} size="sm">Payment Info</Text>
              </Group>
              <Text size="sm" c="dimmed">Amount in Words:</Text>
              <Text size="md" fw={500} style={{ textTransform: 'capitalize' }}>
                {inv.totalInWords || 'Not available'}
              </Text>
            </Card>
          </Grid.Col>

          <Grid.Col span={12}>
            <Title order={6} mt="sm" mb="xs">Itemized Breakdown</Title>
            <Table striped highlightOnHover withTableBorder>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Item</Table.Th>
                  <Table.Th>Qty</Table.Th>
                  <Table.Th>Rate</Table.Th>
                  <Table.Th>Tax</Table.Th>
                  <Table.Th>Total</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {inv.items?.map((item: InvoiceItem, index: number) => (
                  <Table.Tr key={index}>
                    <Table.Td>{item.itemName}</Table.Td>
                    <Table.Td>{item.quantity}</Table.Td>
                    <Table.Td>₹{item.unitPrice}</Table.Td>
                    <Table.Td>₹{item.taxAmount}</Table.Td>
                    <Table.Td fw={700}>₹{item.amount}</Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Grid.Col>
        </Grid>
      </Paper>
    );
  };

  // Invoice table setup
  const invoiceTable = useMantineReactTable({
    columns: invoiceColumns,
    data: invoices,
    enableExpanding: true,
    renderDetailPanel: renderDetailPanel,
    enableEditing: true,
    editDisplayMode: 'row',
    onEditingRowSave: ({ values, row }) => {
      dispatch(updateInvoice({ id: row.original.invoiceId, updates: values }));
    }
  });

  // Product table setup
  const productTable = useMantineReactTable({
    columns: productColumns,
    data: products,
    enableEditing: true,
    enableRowActions: true,
    positionActionsColumn: 'last',
    editDisplayMode: 'row',
    getRowId: row => row.id,
    onEditingRowSave: ({ values, row, table }) => {
      dispatch(updateProduct({ id: row.original.id, updates: values }));
      table.setEditingRow(null);
    }
  });

  // Customer table setup
  const customerTable = useMantineReactTable({
    columns: customerColumns,
    data: customers,
    enableEditing: true,
    editDisplayMode: 'row',
    onEditingRowSave: ({ values, row }) => {
      dispatch(updateCustomer({ id: row.original.id, updates: { ...values } }));
    }
  });

  return (
    <Tabs defaultValue="invoices" variant="outline" radius="md" mt="xl">
      <Tabs.List>
        <Tabs.Tab value="invoices" leftSection={<IconReceipt size={14} />}>Invoices</Tabs.Tab>
        <Tabs.Tab value="products" leftSection={<IconBox size={14} />}>Products</Tabs.Tab>
        <Tabs.Tab value="customers" leftSection={<IconUsers size={14} />}>Customers</Tabs.Tab>
      </Tabs.List>

      <Tabs.Panel value="invoices" pt="md">
        <MantineReactTable table={invoiceTable} />
      </Tabs.Panel>
      <Tabs.Panel value="products" pt="md">
        <MantineReactTable table={productTable} />
      </Tabs.Panel>
      <Tabs.Panel value="customers" pt="md">
        <MantineReactTable table={customerTable} />
      </Tabs.Panel>
    </Tabs>
  );
}
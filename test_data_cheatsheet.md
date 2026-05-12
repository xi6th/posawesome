# POSAwesome Test Data - Quick Reference

## Sample Data Structures

### POS Invoice Example
```json
{
  "doctype": "POS Invoice",
  "customer": "Walk-in Customer",
  "company": "_Test Company",
  "pos_profile": "Test POS Profile",
  "currency": "USD",
  "items": [
    {
      "item_code": "TEST-001",
      "qty": 2,
      "rate": 100
    },
    {
      "item_code": "TEST-002",
      "qty": 1,
      "rate": 250
    }
  ],
  "payments": [
    {
      "mode_of_payment": "Cash",
      "amount": 450
    }
  ]
}
```

### Quotation Example
```json
{
  "doctype": "Quotation",
  "quotation_to": "Customer",
  "customer": "Walk-in Customer",
  "company": "_Test Company",
  "order_type": "Sales",
  "items": [
    {
      "item_code": "TEST-001",
      "qty": 5,
      "rate": 100
    }
  ]
}
```

## Quick API Calls (via Bench Console)

### Create a POS Invoice
```python
from posawesome.posawesome.api import invoice
import json

invoice_data = {
    "doctype": "POS Invoice",
    "customer": "Walk-in Customer",
    "company": "_Test Company",
    "pos_profile": "Test POS Profile",
    "items": [
        {"item_code": "TEST-001", "qty": 2, "rate": 100}
    ],
    "payments": [
        {"mode_of_payment": "Cash", "amount": 200}
    ]
}

result = invoice.create_pos_invoice(json.dumps(invoice_data))
print(f"Invoice created: {result['name']}")
```

### Get Available Items
```python
from posawesome.posawesome.api import items

items_data = items.get_items("Test POS Profile")
print(f"Available items: {len(items_data)}")
```

### Get Customers
```python
from posawesome.posawesome.api import customers

customers = customers.get_customers()
print(f"Total customers: {len(customers)}")
```

### Create a Customer
```python
from posawesome.posawesome.api import customer

new_customer = customer.create_customer({
    "customer_name": "Test Customer",
    "customer_group": "Test POS Customers",
    "territory": "Rest Of The World"
})
```

### Check Stock
```python
from frappe.query_builder import Query

# Get stock balance for TEST-001
from frappe.db import get_value

stock_qty = get_value("Bin", {
    "item_code": "TEST-001",
    "warehouse": "Test Warehouse - _TC"
}, "actual_qty")

print(f"Stock for TEST-001: {stock_qty}")
```

## Test Scenarios

### Scenario 1: Basic Sale
```python
# Create invoice with cash payment
invoice_data = {
    "customer": "Walk-in Customer",
    "items": [{"item_code": "TEST-001", "qty": 1, "rate": 100}],
    "payments": [{"mode_of_payment": "Cash", "amount": 100}]
}
```

### Scenario 2: Split Payment
```python
# Create invoice with multiple payment methods
invoice_data = {
    "customer": "Test Customer 1",
    "items": [
        {"item_code": "TEST-003", "qty": 2, "rate": 500}
    ],
    "payments": [
        {"mode_of_payment": "Cash", "amount": 500},
        {"mode_of_payment": "Credit Card", "amount": 500}
    ]
}
```

### Scenario 3: Return Invoice
```python
# Create a return invoice
return_invoice = {
    "doctype": "POS Invoice",
    "is_return": 1,
    "customer": "Test Customer 1",
    "items": [
        {"item_code": "TEST-001", "qty": -1, "rate": 100}
    ],
    "payments": [
        {"mode_of_payment": "Cash", "amount": -100}
    ]
}
```

### Scenario 4: Mixed Items (Products + Services)
```python
# Invoice with both stock items and services
invoice_data = {
    "customer": "Test Customer 2",
    "items": [
        {"item_code": "TEST-001", "qty": 3, "rate": 100},  # Product
        {"item_code": "TEST-006", "qty": 1, "rate": 150}   # Service
    ],
    "payments": [
        {"mode_of_payment": "Debit Card", "amount": 450}
    ]
}
```

## Verification Queries

### Check All Test Items
```python
test_items = frappe.get_all("Item",
    filters={"item_code": ["like", "TEST-%"]},
    fields=["item_code", "item_name", "is_stock_item", "stock_uom"]
)
for item in test_items:
    print(f"{item.item_code}: {item.item_name}")
```

### Check Stock Levels
```python
from frappe.db import sql

stock_data = sql("""
    SELECT item_code, warehouse, actual_qty
    FROM `tabBin`
    WHERE item_code LIKE 'TEST-%'
""")

for item, warehouse, qty in stock_data:
    print(f"{item}: {qty} units in {warehouse}")
```

### Check Customers
```python
customers = frappe.get_all("Customer",
    filters={"customer_group": "Test POS Customers"},
    fields=["customer_name", "territory"]
)
print(f"Test customers: {len(customers)}")
```

### Check POS Profile
```python
profile = frappe.get_doc("POS Profile", "Test POS Profile")
print(f"Warehouse: {profile.warehouse}")
print(f"Company: {profile.company}")
print(f"Currency: {profile.currency}")
```

## Performance Testing

### Bulk Invoice Creation
```python
import time
from posawesome.posawesome.api import invoice
import json

def create_bulk_invoices(count=10):
    """Create multiple invoices for testing"""
    created = []
    start_time = time.time()

    for i in range(count):
        inv_data = {
            "customer": "Walk-in Customer",
            "items": [
                {"item_code": f"TEST-{(i % 7) + 1:03d}", "qty": 1, "rate": 100}
            ],
            "payments": [
                {"mode_of_payment": "Cash", "amount": 100}
            ]
        }
        result = invoice.create_pos_invoice(json.dumps(inv_data))
        created.append(result['name'])

    elapsed = time.time() - start_time
    print(f"Created {count} invoices in {elapsed:.2f} seconds")
    print(f"Average: {elapsed/count:.2f} seconds per invoice")
    return created

# Run bulk test
invoices = create_bulk_invoices(50)
```

### Load Test Items
```python
from posawesome.posawesome.api import item_fetchers
import time

start = time.time()
items = item_fetchers.get_items_v2("Test POS Profile")
elapsed = time.time() - start

print(f"Fetched {len(items)} items in {elapsed:.2f} seconds")
```

## Common Test Cases

### 1. Test Tax Calculation
```python
invoice_with_tax = {
    "customer": "Walk-in Customer",
    "items": [
        {"item_code": "TEST-004", "qty": 1, "rate": 750}
    ],
    "taxes_and_charges": "Test Sales Tax",
    "payments": [
        {"mode_of_payment": "Cash", "amount": 825}  # 750 + 10% tax
    ]
}
```

### 2. Test Discount
```python
invoice_with_discount = {
    "customer": "Test Customer 1",
    "additional_discount_percentage": 10,
    "items": [
        {"item_code": "TEST-005", "qty": 2, "rate": 1000}
    ],
    "payments": [
        {"mode_of_payment": "Cash", "amount": 1800}  # 2000 - 10%
    ]
}
```

### 3. Test Low Stock Warning
```python
# First, reduce stock manually
# Then try to sell more than available
invoice_low_stock = {
    "customer": "Walk-in Customer",
    "items": [
        {"item_code": "TEST-001", "qty": 150, "rate": 100}  # More than 100 in stock
    ]
}
```

## Debugging Tips

### Enable Logging
```python
import frappe
frappe.logger('posawesome').set_level('DEBUG')
```

### Check Invoice Status
```python
inv = frappe.get_doc("POS Invoice", "INV-00001")
print(f"Status: {inv.status}")
print(f"Docstatus: {inv.docstatus}")
print(f"Grand Total: {inv.grand_total}")
```

### List Recent Invoices
```python
invoices = frappe.get_list("POS Invoice",
    filters={"docstatus": 1},
    fields=["name", "customer", "grand_total", "posting_date"],
    limit=10,
    order_by="creation desc"
)
for inv in invoices:
    print(f"{inv.name}: {inv.customer} - {inv.grand_total}")
```

### Check for Errors
```python
import frappe

# Get error logs
errors = frappe.get_all("Error Log",
    filters={"creation": [">=", "2026-05-11"]},
    fields=["method", "error"],
    limit=10
)
for error in errors:
    print(f"{error.method}: {error.error}")
```

## Cleanup Commands

### Delete Test Invoices
```python
# Get all draft invoices
draft_invoices = frappe.get_list("POS Invoice",
    filters={"docstatus": 0},
    pluck="name"
)

for inv_name in draft_invoices:
    frappe.delete_doc("POS Invoice", inv_name)

print(f"Deleted {len(draft_invoices)} draft invoices")
```

### Cancel Submitted Invoices
```python
submitted_invoices = frappe.get_list("POS Invoice",
    filters={"docstatus": 1},
    pluck="name"
)

for inv_name in submitted_invoices:
    inv = frappe.get_doc("POS Invoice", inv_name)
    if inv.status != "Cancelled":
        inv.cancel()

print(f"Cancelled {len(submitted_invoices)} invoices")
```

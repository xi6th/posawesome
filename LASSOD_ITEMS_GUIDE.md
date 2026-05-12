# Lassod Consulting Limited - Stock Items Guide

Complete guide for creating and managing stock items for Lassod Consulting Limited.

## 🚀 Quick Start

### Method 1: Shell Script (Easiest)
```bash
cd /media/xi6th/Free/Project/Lassod/erp/frappe-bench/apps/posawesome
./create_lassod_items.sh
```

### Method 2: Bench Console
```bash
bench --site [your-site] console
>>> execfile('./apps/posawesome/create_lassod_items.py')
>>> create_lassod_items()
```

## 📦 Items Created (40 Total)

### Office Supplies (10 items)
- A4 Paper (Ream & Box)
- Pens (Blue & Red)
- A4 Hardcover Notebook
- DL Envelopes
- Heavy Duty Stapler
- Plastic File Folders
- Whiteboard Markers
- Desktop Calculator

### Computer Accessories (7 items)
- Wireless Mouse
- USB Keyboard
- USB Headset with Mic
- 1080p HD Webcam
- USB 3.0 Hub (4 Port)
- Adjustable Laptop Stand
- HDMI Extension Cable (2m)

### Network Equipment (5 items)
- CAT6 LAN Cables (5m & 10m)
- 5-Port Network Switch
- Wireless Router
- 24-Port Patch Panel

### Software Licenses (4 items)
- Microsoft 365 Business (Annual)
- Windows 11 Pro License
- Antivirus Business License (Annual)
- Microsoft Teams License (Annual)

### Training Materials (4 items)
- Training Manual (General)
- Training Certificate (Blank)
- ID Card Holder with Lanyard
- Training Starter Kit

### Safety Equipment (3 items)
- Fire Extinguisher (1kg)
- First Aid Kit (50 person)
- High Visibility Safety Vest

## 💰 Pricing (in NGN)

All items are pre-priced in Nigerian Naira:

| Category | Price Range (₦) |
|----------|----------------|
| Office Supplies | 1,500 - 8,500 |
| Computer Accessories | 4,500 - 25,000 |
| Network Equipment | 3,500 - 45,000 |
| Software Licenses | 12,000 - 65,000 |
| Training Materials | 1,500 - 10,000 |
| Safety Equipment | 4,500 - 15,000 |

## 📊 Company Details

- **Company Name**: Lassod Consulting Limited
- **Abbreviation**: LCL
- **Currency**: NGN (₦)
- **Domain**: Consulting
- **Country**: Nigeria

## 🔧 Features

### Automatic Setup
✓ Creates company if not exists
✓ Sets up warehouse (Stores)
✓ Creates item groups
✓ Generates 40 appropriate items
✓ Adds stock (50 units per item)
✓ Creates price list
✓ Sets item prices in NGN

### Item Categories
All items are categorized into 6 logical groups for easy management:
1. Office Supplies - Daily consumables
2. Computer Accessories - IT peripherals
3. Network Equipment - Networking gear
4. Software Licenses - Digital products (no stock)
5. Training Materials - Training supplies
6. Safety Equipment - Safety & compliance

## 📋 Commands Available

### Item Management
```python
create_lassod_items()      # Create all items (recommended first step)
cleanup_lassod_items()     # Delete all Lassod items
list_lassod_items()        # List existing items
```

## ✅ Verification

### Check Items Created
```python
# List all items
>>> list_lassod_items()

# Count items by group
>>> from frappe.db import count
>>> count("Item", {"item_group": "Office Supplies"})

# Check specific item
>>> frappe.get_doc("Item", "A4-PAPER-REAM")
```

### Check Stock Levels
```python
# View stock for all items
>>> from frappe.db import sql

stock_data = sql("""
    SELECT item_code, warehouse, actual_qty
    FROM `tabBin`
    WHERE item_code LIKE '%-%'
    ORDER BY item_code
""")

for item, warehouse, qty in stock_data:
    print(f"{item}: {qty} units in {warehouse}")
```

### Check Prices
```python
# Get item price
>>> from frappe.db import get_value

price = get_value("Item Price",
    {"item_code": "A4-PAPER-REAM"},
    "price_list_rate"
)

print(f"A4 Paper Price: ₦{price}")
```

## 🛠️ Customization

### Add Custom Items
Edit the `get_lassod_items()` function in the script:

```python
{
    "item_code": "CUSTOM-001",
    "item_name": "Your Custom Item",
    "item_group": "Office Supplies",
    "description": "Item description",
    "stock_uom": "Nos",
    "is_stock_item": 1
},
```

### Change Default Stock Quantity
Modify the `qty` parameter in `add_stock_to_item()`:

```python
add_stock_to_item(item_code, warehouse, company, qty=100)  # Instead of 50
```

### Update Prices
Edit the `get_default_rate()` function to change prices:

```python
rates = {
    "A4-PAPER-REAM": 5000,  # Changed from 4500
    # ... other items
}
```

### Add New Item Group
Add to `create_item_groups()`:

```python
{"group_name": "Your Group", "parent": "All Item Groups"},
```

## 🧪 Testing Items

### Create Test Invoice
```python
# Create a sample POS invoice
from posawesome.posawesome.api import invoice
import json

invoice_data = {
    "customer": "Walk-in Customer",
    "company": "Lassod Consulting Limited",
    "items": [
        {"item_code": "A4-PAPER-REAM", "qty": 5, "rate": 4500},
        {"item_code": "PEN-BLUE", "qty": 10, "rate": 1500}
    ],
    "payments": [
        {"mode_of_payment": "Cash", "amount": 37500}
    ]
}

result = invoice.create_pos_invoice(json.dumps(invoice_data))
print(f"Invoice: {result['name']}")
```

### Search for Items
```python
# Search by item code
>>> frappe.get_list("Item",
...     filters={"item_code": ["like", "%PAPER%"]},
...     fields=["item_code", "item_name", "stock_uom"]
... )

# Search by group
>>> frappe.get_list("Item",
...     filters={"item_group": "Computer Accessories"},
...     fields=["item_code", "item_name"]
... )
```

## 📊 Sample Scenarios

### Office Supply Requisition
```python
# Office manager requests supplies
invoice = {
    "customer": "Internal - Office Admin",
    "items": [
        {"item_code": "A4-PAPER-REAM", "qty": 10, "rate": 4500},
        {"item_code": "PEN-BLUE", "qty": 20, "rate": 1500},
        {"item_code": "NOTEBOOK-A4", "qty": 15, "rate": 3500}
    ]
}
```

### IT Equipment Purchase
```python
# IT department orders equipment
invoice = {
    "customer": "Internal - IT Department",
    "items": [
        {"item_code": "MOUSE-WIRELESS", "qty": 5, "rate": 8500},
        {"item_code": "KEYBOARD-USB", "qty": 5, "rate": 9500},
        {"item_code": "HEADSET-USB", "qty": 3, "rate": 18000}
    ]
}
```

### Training Session Kit
```python
# Training coordinator orders materials
invoice = {
    "customer": "Internal - Training Dept",
    "items": [
        {"item_code": "TRAINING-KIT", "qty": 20, "rate": 10000},
        {"item_code": "MANUAL-TRAINING", "qty": 5, "rate": 2500},
        {"item_code": "ID-CARD-HOLDER", "qty": 20, "rate": 2500}
    ]
}
```

## 🔄 Maintenance

### Reorder Levels
Set reorder points for fast-moving items:

```python
# Set reorder level
item = frappe.get_doc("Item", "A4-PAPER-REAM")
item.append("reorder_levels", {
    "warehouse": "Stores - LCL",
    "warehouse_reorder_level": 20,
    "warehouse_reorder_qty": 100
})
item.save()
```

### Stock Updates
Add more stock when needed:

```python
# Add 100 more reams of paper
add_stock_to_item("A4-PAPER-REAM", "Stores - LCL",
                 "Lassod Consulting Limited", qty=100)
```

## 🗑️ Cleanup

### Delete All Items
```python
>>> cleanup_lassod_items()
```

### Delete Specific Item
```python
# Delete specific item and its prices
item_code = "A4-PAPER-REAM"

# Delete prices first
frappe.db.delete("Item Price", {"item_code": item_code})

# Delete item
if frappe.db.exists("Item", item_code):
    frappe.delete_doc("Item", item_code)
```

## 📈 Next Steps

After creating items:
1. **Create POS Profile** - Set up POS profile with these items
2. **Create Users** - Add POS users for Lassod Consulting
3. **Configure Taxes** - Set up Nigerian tax templates
4. **Test POS** - Create test invoices
5. **Train Staff** - Train users on item codes and prices

## 💡 Tips

1. **Item Codes** - Use logical codes like `A4-PAPER-REAM` for easy identification
2. **Groups** - Keep items in appropriate groups for filtering
3. **Stock Levels** - Monitor fast-moving items (A4 paper, pens)
4. **Prices** - Review prices periodically based on market rates
5. **Software** - Track license renewals (set reminders)

## 🔗 Related Files

- **create_lassod_items.py** - Main creation script
- **create_lassod_items.sh** - Shell wrapper script
- **create_pos_user.py** - User management for Lassod
- **test_data_generator.py** - General test data

## ⚠️ Important Notes

- All prices are in Nigerian Naira (₦)
- Software licenses are non-stock items
- Default stock quantity is 50 units per item
- Company abbreviation is "LCL"
- Warehouse name is "Stores - LCL"

## 📞 Support

For issues or questions:
1. Check the script output for error messages
2. Verify company exists: `frappe.db.exists("Company", "Lassod Consulting Limited")`
3. Check item doesn't already exist before creating
4. Review Frappe/Bench logs for detailed errors

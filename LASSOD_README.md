# Lassod Consulting Limited - POS Setup

Complete POS inventory setup for Lassod Consulting Limited.

## 🎯 Overview

This package creates a complete POS-ready inventory system specifically designed for Lassod Consulting Limited, with items priced in Nigerian Naira (₦) and organized for consulting business operations.

## 📦 What's Included

- **40 Stock Items** across 6 categories
- **Company Setup** - Lassod Consulting Limited (Nigeria)
- **Warehouse** - Stores location
- **Item Groups** - 6 logical categories
- **Price List** - All items priced in NGN
- **Stock Management** - 50 units default per item

## 🚀 Quick Start

### Run Setup Script
```bash
cd /media/xi6th/Free/Project/Lassod/erp/frappe-bench/apps/posawesome
./create_lassod_items.sh
```

Choose option 1 to create all items.

### Or Use Bench Console
```bash
bench --site [your-site] console
>>> execfile('./apps/posawesome/create_lassod_items.py')
>>> create_lassod_items()
```

## 📊 Inventory Breakdown

| Category | Items | Examples | Price Range (₦) |
|----------|-------|----------|----------------|
| Office Supplies | 10 | A4 Paper, Pens, Notebooks | 1,500 - 8,500 |
| Computer Accessories | 7 | Mouse, Keyboard, Webcam | 4,500 - 25,000 |
| Network Equipment | 5 | LAN Cables, Router, Switch | 3,500 - 45,000 |
| Software Licenses | 4 | MS 365, Windows 11, Antivirus | 12,000 - 65,000 |
| Training Materials | 4 | Manuals, Certificates, ID Cards | 1,500 - 10,000 |
| Safety Equipment | 3 | Fire Extinguisher, First Aid Kit | 4,500 - 15,000 |

**Total: 40 items**

## 💼 Company Details

- **Name**: Lassod Consulting Limited
- **Abbreviation**: LCL
- **Country**: Nigeria 🇳🇬
- **Currency**: NGN (₦)
- **Domain**: Consulting
- **Warehouse**: Stores - LCL

## 🎁 Key Features

✅ **Consulting-Focused** - Items selected for consulting operations
✅ **Naira Pricing** - All prices in Nigerian Naira
✅ **Organized Categories** - 6 logical groups for easy management
✅ **Pre-Stocked** - 50 units per item ready for sale
✅ **Complete Descriptions** - Clear item descriptions
✅ **Standard UoM** - Common units of measure
✅ **Non-Stock Items** - Software licenses configured correctly

## 📋 Sample Items

### Office Supplies
- A4 Paper - Ream (₦4,500)
- Blue Ballpoint Pen - Pack (₦1,500)
- A4 Hardcover Notebook (₦3,500)
- Desktop Calculator (₦8,500)

### IT Equipment
- Wireless Mouse (₦8,500)
- USB Keyboard (₦9,500)
- 1080p HD Webcam (₦25,000)
- CAT6 LAN Cable - 5m (₦3,500)

### Software Licenses
- Microsoft 365 Business - Annual (₦45,000)
- Windows 11 Pro License (₦65,000)
- Antivirus Business - Annual (₦12,000)

## 🛠️ Management Commands

### Create Items
```bash
./create_lassod_items.sh
# Choose option 1
```

### List Items
```bash
./create_lassod_items.sh
# Choose option 2
```

### Clean Up
```bash
./create_lassod_items.sh
# Choose option 3
```

### View Categories
```bash
./create_lassod_items.sh
# Choose option 4
```

## 🔧 Customization

### Add Custom Items
Edit `create_lassod_items.py` and add to `get_lassod_items()`:

```python
{
    "item_code": "YOUR-ITEM-001",
    "item_name": "Your Item Name",
    "item_group": "Office Supplies",
    "description": "Item description",
    "stock_uom": "Nos",
    "is_stock_item": 1
},
```

### Change Prices
Edit the `get_default_rate()` function:

```python
rates = {
    "A4-PAPER-REAM": 5000,  # Update price
    # ... other items
}
```

### Adjust Stock Levels
Modify in `add_stock_to_item()`:

```python
add_stock_to_item(item_code, warehouse, company, qty=100)  # Instead of 50
```

## ✅ Verification

### Check Items Created
```python
bench --site [site] console
>>> execfile('./apps/posawesome/create_lassod_items.py')
>>> list_lassod_items()
```

### Check Company
```python
>>> frappe.get_doc("Company", "Lassod Consulting Limited")
```

### View Stock
```python
>>> from frappe.db import sql
>>> sql("SELECT item_code, actual_qty FROM `tabBin` WHERE warehouse LIKE '%LCL%'")
```

## 📈 Next Steps

### 1. Create POS Profile
Set up POS profile with Lassod items:
```python
# In bench console
>>> pos_profile = frappe.get_doc({
...     "doctype": "POS Profile",
...     "pos_profile_name": "Lassod POS",
...     "company": "Lassod Consulting Limited",
...     "warehouse": "Stores - LCL",
...     # ... configure other settings
... }).insert()
```

### 2. Add Users
Create POS users for Lassod:
```bash
./create_user.sh
```

### 3. Configure Taxes
Set up Nigerian tax templates:
```python
# Create 5% VAT template for consulting
tax_template = frappe.get_doc({
    "doctype": "Sales Taxes and Charges Template",
    "title": "Nigeria VAT 5%",
    "company": "Lassod Consulting Limited",
    "taxes": [{
        "charge_type": "On Net Total",
        "account_head": "Output Tax - LCL",
        "rate": 5
    }]
}).insert()
```

### 4. Test POS
Create test invoices:
```python
from posawesome.posawesome.api import invoice
import json

invoice_data = {
    "customer": "Walk-in Customer",
    "company": "Lassod Consulting Limited",
    "items": [
        {"item_code": "A4-PAPER-REAM", "qty": 5, "rate": 4500}
    ],
    "payments": [
        {"mode_of_payment": "Cash", "amount": 22500}
    ]
}

result = invoice.create_pos_invoice(json.dumps(invoice_data))
```

## 📚 Documentation

- **LASSOD_ITEMS_GUIDE.md** - Detailed item management guide
- **create_lassod_items.py** - Main Python script (22K)
- **create_lassod_items.sh** - Shell wrapper (4.5K)

## 💡 Usage Tips

1. **Item Codes** - Use descriptive codes like `A4-PAPER-REAM` for easy lookup
2. **Stock Monitoring** - Fast-moving items: A4 paper, pens, notebooks
3. **Software Licenses** - Track renewal dates (non-stock items)
4. **Price Updates** - Review quarterly based on market rates
5. **Categories** - Use groups for filtering in POS

## 🔄 Maintenance

### Reorder Points
Set reorder levels for fast items:
```python
item = frappe.get_doc("Item", "A4-PAPER-REAM")
item.append("reorder_levels", {
    "warehouse": "Stores - LCL",
    "warehouse_reorder_level": 20,
    "warehouse_reorder_qty": 100
})
item.save()
```

### Stock Updates
Add stock when needed:
```python
execfile('./apps/posawesome/create_lassod_items.py')
add_stock_to_item("A4-PAPER-REAM", "Stores - LCL",
                 "Lassod Consulting Limited", qty=100)
```

## 🗑️ Cleanup

Delete all Lassod items:
```python
>>> execfile('./apps/posawesome/create_lassod_items.py')
>>> cleanup_lassod_items()
```

## ⚠️ Important Notes

- All prices in Nigerian Naira (₦)
- Default stock: 50 units per item
- Software licenses are non-stock items
- Company must exist before running
- Some items may need account configuration

## 📞 Support

For issues:
1. Check script output for errors
2. Verify company exists
3. Check item doesn't already exist
4. Review Frappe/Bench logs

## 🎉 Ready to Use

After running the setup, your POS will have:
- ✅ 40 ready-to-sell items
- ✅ Prices in Naira
- ✅ Stock in warehouse
- ✅ Organized categories
- ✅ Complete descriptions

Perfect for consulting operations!

---

**Created for**: Lassod Consulting Limited 🇳🇬
**Items**: 40 | **Categories**: 6 | **Currency**: NGN

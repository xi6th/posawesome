# POSAwesome Test Data Generator - Quick Start Guide

## Overview
This script generates comprehensive test data for POSAwesome development and testing, including:
- Warehouse with stock
- Products and services
- Customers
- Tax templates and price lists
- POS profile
- Payment methods
- Test users

## Prerequisites
- Working Frappe bench setup
- POSAwesome app installed
- Site configured

## Usage

### Method 1: Run in Bench Console (Recommended)

```bash
# Navigate to your bench directory
cd /path/to/frappe-bench

# Start bench console for your site
bench --site [your-site-name] console

# In the console, run:
execfile('./apps/posawesome/test_data_generator.py')
```

**Example:**
```bash
cd ~/frappe-bench
bench --site mysite.local console
>>> execfile('./apps/posawesome/test_data_generator.py')
```

### Method 2: Import as Module

```bash
bench --site [site-name] console
>>> import sys
>>> sys.path.append('./apps/posawesome')
>>> import test_data_generator
>>> test_data_generator.create_test_data()
```

### Clean Up Test Data

To remove all generated test data:

```bash
bench --site [site-name] console
>>> execfile('./apps/posawesome/test_data_generator.py')
>>> test_data_generator.cleanup_test_data()
```

Or run with cleanup argument:
```bash
cd /path/to/frappe-bench/apps/posawesome
python3 test_data_generator.py cleanup
```

## Generated Data

### Items (7 total)
- TEST-001 to TEST-005: Physical products with stock
- TEST-006 to TEST-007: Services
- All items have 100 units in stock (except services)

### Customers (4 total)
- Walk-in Customer (default)
- Test Customer 1, 2, 3

### Payment Methods
- Cash
- Credit Card
- Debit Card
- Mobile Payment

### Users
- pos_cashier@test.com (Cashier role)
- pos_manager@test.com (Accounts Manager role)

### Configuration
- Warehouse: Test Warehouse
- Customer Group: Test POS Customers
- Tax Template: 10% sales tax
- Price List: Test POS Price List
- POS Profile: Test POS Profile

## Testing the POS

After running the script, you can:

1. **Access POS**: Open `/app/pos` in your browser
2. **Login as Cashier**: Use `pos_cashier@test.com`
3. **Select Profile**: Choose "Test POS Profile"
4. **Create Invoice**: Add items from TEST-001 to TEST-007
5. **Select Customer**: Choose from test customers
6. **Payment**: Select from payment methods

## Common Issues

### "Account not found" Errors
The script uses `_Test Company` which should have default accounts. If you get account errors:
```python
# In bench console, list available companies
frappe.get_list("Company")

# Update the company name in the script if needed
```

### Stock Entry Errors
If stock creation fails:
```python
# Check if warehouse exists
frappe.db.exists("Warehouse", "Test Warehouse - _TC")

# Verify stock_uom exists
frappe.db.exists("UOM", "Nos")
```

### Permission Errors
Make sure you're logged in as Administrator:
```bash
bench --site [site-name] login administrator
```

## Customization

### Add More Items
Edit the `item_templates` list in `create_items()`:
```python
{"item_code": "TEST-008", "item_name": "My Product", "item_group": "Test Product Group", "rate": 1500}
```

### Change Stock Quantity
Modify the `qty` parameter in `add_stock_to_item()`:
```python
add_stock_to_item(item_code, warehouse, qty=500)  # Instead of 100
```

### Different Tax Rates
Update the `taxes` list in `create_tax_template()`:
```python
{"charge_type": "On Net Total", "account_head": "Output Tax - _TC", "rate": 15}
```

## Manual Data Creation (Alternative)

If you prefer creating data through UI:

1. Go to `/app/item` and create items
2. Go to `/app/customer` and create customers
3. Go to `/app/warehouse` and create warehouse
4. Go to `/app/stock-entry` to add stock
5. Go to `/app/pos-profile` to configure POS

## Troubleshooting

### Script Won't Run
- Check Python path is correct
- Verify site is running: `bench start`
- Check file permissions: `chmod +x test_data_generator.py`

### Duplicate Data
Run cleanup first:
```python
>>> execfile('./apps/posawesome/test_data_generator.py')
>>> test_data_generator.cleanup_test_data()
>>> test_data_generator.create_test_data()
```

### Database Lock
Wait a few seconds and retry, or restart bench:
```bash
bench restart
```

## Next Steps

After test data is created:
1. Configure additional POS profiles as needed
2. Set up barcodes for items (optional)
3. Configure printers for receipts
4. Test offline sync
5. Run test suites: `bench --site [site] run-tests --app posawesome`

## Support

For issues with:
- **Frappe Framework**: Check https://frappeframework.com/docs
- **POSAwesome**: Check https://github.com/yrestom/POS-Awesome/issues

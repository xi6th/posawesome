# POSAwesome Test Data Suite

Complete test data generation and testing toolkit for POSAwesome development.

## 📦 What's Included

- **test_data_generator.py** - Main Python script to generate test data
- **setup_test_data.sh** - Bash wrapper script for easy execution
- **TEST_DATA_GUIDE.md** - Comprehensive setup and usage guide
- **test_data_cheatsheet.md** - Quick reference with API examples and test scenarios

## 🚀 Quick Start

### Option 1: Using the Shell Script (Easiest)

```bash
cd /path/to/frappe-bench/apps/posawesome
./setup_test_data.sh
```

Follow the prompts to:
1. Select your site
2. Choose to generate, cleanup, or re-generate test data

### Option 2: Manual Execution

```bash
# Navigate to bench directory
cd /path/to/frappe-bench

# Start bench console
bench --site [your-site] console

# Run the generator
>>> execfile('./apps/posawesome/test_data_generator.py')
>>> create_test_data()
```

## 📊 Generated Test Data

### Core Entities
- **7 Items** (5 products + 2 services) with 100 units stock each
- **4 Customers** (1 Walk-in + 3 named customers)
- **1 Warehouse** with stock management
- **4 Payment Methods** (Cash, Credit Card, Debit Card, Mobile)
- **2 POS Users** (Cashier and Manager roles)
- **1 POS Profile** with complete configuration
- **Tax Template** (10% sales tax)
- **Price List** with item prices

### Test Users
- **Cashier**: pos_cashier@test.com (Cashier role)
- **Manager**: pos_manager@test.com (Accounts Manager role)
- **Default**: Administrator (your admin account)

## 🧪 Testing Scenarios

All scenarios are documented in **test_data_cheatsheet.md**:

1. **Basic Sale** - Simple cash transaction
2. **Split Payment** - Multiple payment methods
3. **Return Invoice** - Process returns
4. **Mixed Items** - Products + services
5. **Tax Calculation** - Verify tax computation
6. **Discount Application** - Test discount logic
7. **Low Stock Warnings** - Inventory validation
8. **Bulk Operations** - Performance testing

## 📚 Documentation

### TEST_DATA_GUIDE.md
- Detailed setup instructions
- Troubleshooting common issues
- Customization guide
- Manual data creation alternatives

### test_data_cheatsheet.md
- Sample JSON structures
- API call examples
- Test scenarios with code
- Verification queries
- Performance testing scripts
- Debugging tips
- Cleanup commands

## 🛠️ Advanced Usage

### Custom Item Data
Edit `test_data_generator.py` and modify the `item_templates` list:

```python
item_templates = [
    {"item_code": "CUSTOM-001", "item_name": "My Product", "item_group": "My Group", "rate": 1999},
    # Add more items...
]
```

### Different Stock Levels
Modify the `add_stock_to_item()` call:

```python
add_stock_to_item(item_code, warehouse, qty=500)  # Default is 100
```

### Custom Tax Rates
Update the `create_tax_template()` function:

```python
{
    "charge_type": "On Net Total",
    "account_head": "Output Tax - _TC",
    "rate": 15  # Change from 10% to 15%
}
```

## 🧹 Cleanup

### Using Shell Script
```bash
./setup_test_data.sh
# Choose option 2: Clean up test data
```

### Using Bench Console
```python
>>> execfile('./apps/posawesome/test_data_generator.py')
>>> cleanup_test_data()
```

### Manual Cleanup
```python
# Delete specific entities
frappe.delete_doc("Item", "TEST-001")
frappe.delete_doc("Customer", "Test Customer 1")
# etc.
```

## ⚠️ Common Issues

### "Account not found" Error
- Ensure `_Test Company` exists with default accounts
- Or update company name in the script

### "Warehouse not found" Error
- Verify warehouse was created successfully
- Check `frappe.db.exists("Warehouse", "Test Warehouse - _TC")`

### Stock Entry Failures
- Verify stock_uom "Nos" exists
- Check warehouse is valid
- Ensure accounts are configured

### Permission Errors
- Run as Administrator user
- Check user has necessary permissions

## 🎯 Next Steps

1. **Verify Data** - Check all entities in Desk UI
2. **Test POS** - Open `/app/pos` and create invoices
3. **Run Tests** - Execute test suite: `bench --site [site] run-tests --app posawesome`
4. **Customize** - Add more data as needed
5. **Develop** - Start building features with confidence

## 📖 Additional Resources

- [POSAwesome GitHub](https://github.com/yrestom/POS-Awesome)
- [Frappe Framework Docs](https://frappeframework.com/docs)
- [Frappe API Reference](https://frappeframework.com/docs/v13/user/en/api)
- [ERPNext Docs](https://docs.erpnext.com)

## 🤝 Contributing

When contributing to POSAwesome, please:
1. Use this test data for development
2. Add test scenarios to the cheatsheet
3. Document new data requirements
4. Update this README if needed

## 📝 License

This test data suite is part of POSAwesome and follows the same license.

---

**Need Help?** Check the individual documentation files or open an issue on GitHub.

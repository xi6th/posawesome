#!/usr/bin/env python3
"""
Test Data Generator for POSAwesome
Run this script in bench console to generate test data:
bench --site [site_name] console
>>> execfile('/path/to/test_data_generator.py')
"""

import frappe
from frappe.utils import getdate, add_days, random_string
from random import randint, choice

def create_test_data():
    """Create all test data for POSAwesome testing"""

    print("Starting POSAwesome test data generation...")

    # 1. Create Warehouse
    warehouse = create_warehouse()
    print(f"✓ Created warehouse: {warehouse}")

    # 2. Create Items
    items = create_items(warehouse)
    print(f"✓ Created {len(items)} items")

    # 3. Create Customer Group
    customer_group = create_customer_group()
    print(f"✓ Created customer group: {customer_group}")

    # 4. Create Customers
    customers = create_customers(customer_group)
    print(f"✓ Created {len(customers)} customers")

    # 5. Create Tax Template
    tax_template = create_tax_template()
    print(f"✓ Created tax template: {tax_template}")

    # 6. Create Price List
    price_list = create_price_list()
    print(f"✓ Created price list: {price_list}")

    # 7. Create Item Prices
    create_item_prices(items, price_list)
    print(f"✓ Created item prices")

    # 8. Create POS Profile
    pos_profile = create_pos_profile(warehouse, tax_template, price_list)
    print(f"✓ Created POS profile: {pos_profile}")

    # 9. Create Payment Methods
    payment_methods = create_payment_methods()
    print(f"✓ Created {len(payment_methods)} payment methods")

    # 10. Create Users (optional)
    users = create_pos_users()
    print(f"✓ Created {len(users)} POS users")

    print("\n✅ Test data generation complete!")
    print(f"\nTest Data Summary:")
    print(f"  - Warehouse: {warehouse}")
    print(f"  - Items: {len(items)}")
    print(f"  - Customers: {len(customers)}")
    print(f"  - POS Profile: {pos_profile}")
    print(f"  - Payment Methods: {len(payment_methods)}")
    print(f"  - POS Users: {len(users)}")

    return {
        'warehouse': warehouse,
        'items': items,
        'customers': customers,
        'pos_profile': pos_profile,
        'payment_methods': payment_methods,
        'users': users
    }

def create_warehouse():
    """Create a test warehouse"""
    warehouse_name = "Test Warehouse - POS"

    if frappe.db.exists("Warehouse", warehouse_name):
        frappe.delete_doc("Warehouse", warehouse_name)
        frappe.db.commit()

    warehouse = frappe.get_doc({
        "doctype": "Warehouse",
        "warehouse_name": "Test Warehouse",
        "is_group": 0,
        "parent_warehouse": "All Warehouses - _TC",
        "company": "_Test Company",
        "account": "_Test Warehouse - _TC"
    }).insert()

    return warehouse.name

def create_items(warehouse):
    """Create test items"""
    item_templates = [
        {"item_code": "TEST-001", "item_name": "Test Product 1", "item_group": "Test Product Group", "rate": 100},
        {"item_code": "TEST-002", "item_name": "Test Product 2", "item_group": "Test Product Group", "rate": 250},
        {"item_code": "TEST-003", "item_name": "Test Product 3", "item_group": "Test Product Group", "rate": 500},
        {"item_code": "TEST-004", "item_name": "Test Product 4", "item_group": "Test Product Group", "rate": 750},
        {"item_code": "TEST-005", "item_name": "Test Product 5", "item_group": "Test Product Group", "rate": 1000},
        {"item_code": "TEST-006", "item_name": "Test Service 1", "item_group": "Services", "rate": 150},
        {"item_code": "TEST-007", "item_name": "Test Service 2", "item_group": "Services", "rate": 300},
    ]

    items = []
    for item_data in item_templates:
        item_code = item_data['item_code']

        # Delete if exists
        if frappe.db.exists("Item", item_code):
            frappe.delete_doc("Item", item_code)
            frappe.db.commit()

        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": item_data['item_name'],
            "item_group": item_data['item_group'],
            "description": f"Test {item_data['item_name']} for POS testing",
            "stock_uom": "Nos",
            "is_stock_item": 1 if "Product" in item_data['item_name'] else 0,
            "include_item_in_manufacturing": 0,
            "default_warehouse": warehouse,
            "item_defaults": [
                {
                    "company": "_Test Company",
                    "default_warehouse": warehouse,
                    "expense_account": "Cost of Goods Sold - _TC",
                    "income_account": "Sales - _TC",
                    "buying_cost_center": "Main - _TC",
                    "selling_cost_center": "Main - _TC"
                }
            ]
        }).insert()

        items.append(item.name)

        # Add stock for stock items
        if item.is_stock_item:
            add_stock_to_item(item_code, warehouse, qty=100)

    return items

def add_stock_to_item(item_code, warehouse, qty=100):
    """Add stock to item"""
    try:
        stock_entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "items": [{
                "item_code": item_code,
                "qty": qty,
                "to_warehouse": warehouse,
                "uom": "Nos"
            }],
            "company": "_Test Company"
        })
        stock_entry.submit()
    except Exception as e:
        print(f"Note: Could not add stock to {item_code}: {e}")

def create_customer_group():
    """Create customer group"""
    group_name = "Test POS Customers"

    if frappe.db.exists("Customer Group", group_name):
        frappe.delete_doc("Customer Group", group_name)
        frappe.db.commit()

    customer_group = frappe.get_doc({
        "doctype": "Customer Group",
        "customer_group_name": group_name,
        "parent_customer_group": "All Customer Groups"
    }).insert()

    return customer_group.name

def create_customers(customer_group):
    """Create test customers"""
    customers_data = [
        {"customer_name": "Walk-in Customer", "territory": "Rest Of The World"},
        {"customer_name": "Test Customer 1", "territory": "Rest Of The World"},
        {"customer_name": "Test Customer 2", "territory": "Rest Of The World"},
        {"customer_name": "Test Customer 3", "territory": "Rest Of The World"},
    ]

    customers = []
    for customer_data in customers_data:
        customer_name = customer_data['customer_name']

        # Delete if exists (skip Walk-in Customer as it might be system default)
        if customer_name != "Walk-in Customer" and frappe.db.exists("Customer", customer_name):
            frappe.delete_doc("Customer", customer_name)
            frappe.db.commit()

        customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": customer_name,
            "customer_group": customer_group,
            "territory": customer_data['territory'],
            "customer_type": "Individual",
            "default_currency": "USD",
            "accounts": [{
                "company": "_Test Company",
                "account": "Debtors - _TC"
            }]
        }).insert()

        customers.append(customer.name)

    return customers

def create_tax_template():
    """Create sales tax template"""
    template_name = "Test Sales Tax"

    if frappe.db.exists("Sales Taxes and Charges Template", template_name):
        frappe.delete_doc("Sales Taxes and Charges Template", template_name)
        frappe.db.commit()

    tax_template = frappe.get_doc({
        "doctype": "Sales Taxes and Charges Template",
        "title": template_name,
        "is_default": 1,
        "company": "_Test Company",
        "taxes": [
            {
                "charge_type": "On Net Total",
                "account_head": "Output Tax - _TC",
                "rate": 10,
                "description": "Test Tax 10%"
            }
        ]
    }).insert()

    return tax_template.name

def create_price_list():
    """Create price list"""
    price_list_name = "Test POS Price List"

    if frappe.db.exists("Price List", price_list_name):
        frappe.delete_doc("Price List", price_list_name)
        frappe.db.commit()

    price_list = frappe.get_doc({
        "doctype": "Price List",
        "price_list_name": price_list_name,
        "currency": "USD",
        "enabled": 1,
        "selling": 1
    }).insert()

    return price_list.name

def create_item_prices(items, price_list):
    """Create item prices"""
    for item_code in items:
        item_price = frappe.get_doc({
            "doctype": "Item Price",
            "price_list": price_list,
            "item_code": item_code,
            "price_list_rate": randint(50, 2000)
        }).insert()

        frappe.db.commit()

def create_pos_profile(warehouse, tax_template, price_list):
    """Create POS profile"""
    profile_name = "Test POS Profile"

    if frappe.db.exists("POS Profile", profile_name):
        frappe.delete_doc("POS Profile", profile_name)
        frappe.db.commit()

    pos_profile = frappe.get_doc({
        "doctype": "POS Profile",
        "pos_profile_name": profile_name,
        "company": "_Test Company",
        "warehouse": warehouse,
        "currency": "USD",
        "write_off_account": "Exchange Gain/Loss - _TC",
        "write_off_cost_center": "Main - _TC",
        "customer_group": "Test POS Customers",
        "taxes": [tax_template],
        "stock_lookup_location": warehouse,
        "allow_returns": 1,
        "check_stock_for_inwards": 1
    }).insert()

    return pos_profile.name

def create_payment_methods():
    """Create payment methods"""
    payment_methods_data = [
        {"mode_of_payment": "Cash", "type": "Cash"},
        {"mode_of_payment": "Credit Card", "type": "General"},
        {"mode_of_payment": "Debit Card", "type": "General"},
        {"mode_of_payment": "Mobile Payment", "type": "General"}
    ]

    payment_methods = []
    for payment_data in payment_methods_data:
        mode_name = payment_data['mode_of_payment']

        # Delete if exists
        if frappe.db.exists("Mode of Payment", mode_name):
            frappe.delete_doc("Mode of Payment", mode_name)
            frappe.db.commit()

        mode = frappe.get_doc({
            "doctype": "Mode of Payment",
            "mode_of_payment": mode_name,
            "type": payment_data['type'],
            "enabled": 1,
            "accounts": [{
                "company": "_Test Company",
                "default_account": "Cash - _TC" if payment_data['type'] == 'Cash' else "Bank - _TC"
            }]
        }).insert()

        payment_methods.append(mode.name)

    return payment_methods

def create_pos_users():
    """Create POS users"""
    users_data = [
        {"email": "pos_cashier@test.com", "first_name": "POS", "last_name": "Cashier", "role": "Cashier"},
        {"email": "pos_manager@test.com", "first_name": "POS", "last_name": "Manager", "role": "Accounts Manager"}
    ]

    users = []
    for user_data in users_data:
        email = user_data['email']

        # Delete if exists
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email)
            frappe.db.commit()

        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": user_data['first_name'],
            "last_name": user_data['last_name'],
            "send_welcome_email": 0,
            "roles": [{
                "role": user_data['role']
            }]
        }).insert()

        users.append(user.email)

    return users

def cleanup_test_data():
    """Clean up all test data"""
    print("\nCleaning up test data...")

    # Clean up in reverse order of dependencies
    cleanup_list = [
        ("User", ["pos_cashier@test.com", "pos_manager@test.com"]),
        ("Mode of Payment", ["Cash", "Credit Card", "Debit Card", "Mobile Payment"]),
        ("POS Profile", ["Test POS Profile"]),
        ("Item Price", None),  # Will query all test items
        ("Price List", ["Test POS Price List"]),
        ("Sales Taxes and Charges Template", ["Test Sales Tax"]),
        ("Customer", ["Test Customer 1", "Test Customer 2", "Test Customer 3"]),
        ("Customer Group", ["Test POS Customers"]),
        ("Item", ["TEST-001", "TEST-002", "TEST-003", "TEST-004", "TEST-005", "TEST-006", "TEST-007"]),
        ("Warehouse", ["Test Warehouse - _TC"])
    ]

    for doctype, names in cleanup_list:
        if names:
            for name in names:
                if frappe.db.exists(doctype, name):
                    try:
                        frappe.delete_doc(doctype, name)
                        print(f"✓ Deleted {doctype}: {name}")
                    except Exception as e:
                        print(f"✗ Could not delete {doctype} {name}: {e}")
        elif doctype == "Item Price" and names is None:
            # Delete all item prices for test items
            test_items = ["TEST-001", "TEST-002", "TEST-003", "TEST-004", "TEST-005", "TEST-006", "TEST-007"]
            for item_code in test_items:
                item_prices = frappe.get_all("Item Price", filters={"item_code": item_code})
                for price in item_prices:
                    try:
                        frappe.delete_doc("Item Price", price.name)
                        print(f"✓ Deleted Item Price: {price.name}")
                    except Exception as e:
                        print(f"✗ Could not delete Item Price {price.name}: {e}")

    frappe.db.commit()
    print("\n✅ Cleanup complete!")

# Main execution
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_test_data()
    else:
        create_test_data()

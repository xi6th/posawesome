#!/usr/bin/env python3
import sys
import os

# Add the app to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Initialize Frappe
import frappe
frappe.init(site='lassod')
frappe.connect()

try:
    # Import and run the function
    from apps.posawesome.create_lassod_items import create_lassod_items
    result = create_lassod_items()

    print("\n" + "="*60)
    print("Summary:")
    print(f"  Company: {result['company']}")
    print(f"  Warehouse: {result['warehouse']}")
    print(f"  Items created: {len(result['items'])}")
    print(f"  Price list: {result['price_list']}")
    print("="*60)

finally:
    frappe.destroy()

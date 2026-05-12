#!/usr/bin/env python3
"""
Create Stock Items for Lassod Consulting Limited
Run in bench console: bench --site lassod console
>>> execfile('./apps/posawesome/create_lassod_items.py')
"""

import frappe
from frappe.utils import getdate, random_string

def create_lassod_items():
    """Create stock items for Lassod Consulting Limited"""

    company = "Lassod Consulting Limited"
    print(f"\n{'='*60}")
    print(f"Creating Stock Items for {company}")
    print(f"{'='*60}\n")

    # Check if company exists
    if not frappe.db.exists("Company", company):
        print(f"⚠ Company '{company}' not found!")
        print(f"   Creating company first...")

        # Create the company
        create_lassod_company()

    # Get or create warehouse
    warehouse = get_or_create_warehouse(company)
    print(f"✓ Using warehouse: {warehouse}\n")

    # Create item groups
    item_groups = create_item_groups()
    print(f"✓ Created item groups: {', '.join(item_groups)}\n")

    # Create items
    items_data = get_lassod_items()
    created_items = []

    for item_data in items_data:
        item_code = item_data['item_code']

        # Check if item exists
        if frappe.db.exists("Item", item_code):
            print(f"⚠ Item {item_code} already exists, skipping...")
            continue

        try:
            # Create item
            item = create_item(item_data, warehouse, company)
            created_items.append(item.name)
            print(f"✓ Created: {item_code} - {item_data['item_name']}")
        except Exception as e:
            print(f"✗ Failed to create {item_code}: {e}")

    # Add stock to items
    print(f"\n{'='*60}")
    print("Adding Stock to Items")
    print(f"{'='*60}\n")

    for item_code in created_items:
        item = frappe.get_doc("Item", item_code)
        if item.is_stock_item:
            add_stock_to_item(item_code, warehouse, company, qty=50)
            print(f"✓ Added stock to {item_code}")

    # Create price list
    price_list = create_price_list(company)
    print(f"\n✓ Created price list: {price_list}")

    # Create item prices
    print(f"\n{'='*60}")
    print("Setting Item Prices")
    print(f"{'='*60}\n")

    for item_code in created_items:
        item = frappe.get_doc("Item", item_code)
        if item.stock_uom == "Nos":
            # Set a default price
            rate = get_default_rate(item_code)
            create_item_price(item_code, price_list, rate)
            print(f"✓ Set price for {item_code}: {rate}")

    print(f"\n{'='*60}")
    print(f"✅ Successfully created {len(created_items)} items for {company}")
    print(f"{'='*60}\n")

    return {
        'company': company,
        'warehouse': warehouse,
        'items': created_items,
        'price_list': price_list,
        'item_groups': item_groups
    }

def create_lassod_company():
    """Create Lassod Consulting Limited company"""

    company = frappe.get_doc({
        "doctype": "Company",
        "company_name": "Lassod Consulting Limited",
        "abbr": "LCL",
        "country": "Nigeria",
        "default_currency": "NGN",
        "domain": "Consulting",
        "chart_of_accounts": "Standard",
        "enable_perpetual_inventory": 1
    })

    company.insert()
    print(f"✓ Created company: {company.name}")

    return company

def get_or_create_warehouse(company):
    """Get or create warehouse for the company"""

    warehouse_name = f"Stores - {frappe.get_doc('Company', company).abbr}"

    if frappe.db.exists("Warehouse", warehouse_name):
        return warehouse_name

    warehouse = frappe.get_doc({
        "doctype": "Warehouse",
        "warehouse_name": "Stores",
        "is_group": 0,
        "parent_warehouse": "All Warehouses",
        "company": company
    }).insert()

    return warehouse.name

def create_item_groups():
    """Create item groups for consulting business"""

    groups_data = [
        {"group_name": "Office Supplies", "parent": "All Item Groups"},
        {"group_name": "Computer Accessories", "parent": "All Item Groups"},
        {"group_name": "Network Equipment", "parent": "All Item Groups"},
        {"group_name": "Software Licenses", "parent": "All Item Groups"},
        {"group_name": "Training Materials", "parent": "All Item Groups"},
        {"group_name": "Safety Equipment", "parent": "All Item Groups"},
    ]

    created_groups = []

    for group_data in groups_data:
        group_name = group_data['group_name']

        if not frappe.db.exists("Item Group", group_name):
            group = frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": group_name,
                "parent_item_group": group_data['parent'],
                "is_group": 0
            }).insert()

            created_groups.append(group.name)
        else:
            created_groups.append(group_name)

    return created_groups

def get_lassod_items():
    """Get list of items suitable for consulting business"""

    items = [
        # Office Supplies
        {
            "item_code": "A4-PAPER-REAM",
            "item_name": "A4 Paper - Ream",
            "item_group": "Office Supplies",
            "description": "Quality A4 printing paper, 500 sheets per ream",
            "stock_uom": "Ream",
            "is_stock_item": 1
        },
        {
            "item_code": "A4-PAPER-BOX",
            "item_name": "A4 Paper - Box",
            "item_group": "Office Supplies",
            "description": "A4 printing paper, 10 reams per box",
            "stock_uom": "Box",
            "is_stock_item": 1
        },
        {
            "item_code": "PEN-BLUE",
            "item_name": "Blue Ballpoint Pen",
            "item_group": "Office Supplies",
            "description": "Blue ink ballpoint pen, pack of 10",
            "stock_uom": "Pack",
            "is_stock_item": 1
        },
        {
            "item_code": "PEN-RED",
            "item_name": "Red Ballpoint Pen",
            "item_group": "Office Supplies",
            "description": "Red ink ballpoint pen, pack of 10",
            "stock_uom": "Pack",
            "is_stock_item": 1
        },
        {
            "item_code": "NOTEBOOK-A4",
            "item_name": "A4 Hardcover Notebook",
            "item_group": "Office Supplies",
            "description": "A4 size hardcover notebook, 200 pages",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "ENVELOPE-DL",
            "item_name": "DL Envelope - Box",
            "item_group": "Office Supplies",
            "description": "DL size window envelopes, 500 per box",
            "stock_uom": "Box",
            "is_stock_item": 1
        },
        {
            "item_code": "STAPLER",
            "item_name": "Heavy Duty Stapler",
            "item_group": "Office Supplies",
            "description": "Heavy duty stapler with 1000 staples",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "FILE-FOLDER",
            "item_name": "Plastic File Folder",
            "item_group": "Office Supplies",
            "description": "Plastic file folder, assorted colors, pack of 20",
            "stock_uom": "Pack",
            "is_stock_item": 1
        },
        {
            "item_code": "MARKER-BLACK",
            "item_name": "Whiteboard Marker - Black",
            "item_group": "Office Supplies",
            "description": "Black whiteboard marker, pack of 5",
            "stock_uom": "Pack",
            "is_stock_item": 1
        },
        {
            "item_code": "CALCULATOR",
            "item_name": "Desktop Calculator",
            "item_group": "Office Supplies",
            "description": "12-digit desktop calculator with dual power",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },

        # Computer Accessories
        {
            "item_code": "MOUSE-WIRELESS",
            "item_name": "Wireless Mouse",
            "item_group": "Computer Accessories",
            "description": "2.4GHz wireless optical mouse with USB receiver",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "KEYBOARD-USB",
            "item_name": "USB Keyboard",
            "item_group": "Computer Accessories",
            "description": "Standard USB keyboard, UK layout",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "HEADSET-USB",
            "item_name": "USB Headset with Microphone",
            "item_group": "Computer Accessories",
            "description": "USB headset with noise-cancelling microphone",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "WEBCAM-1080P",
            "item_name": "1080p HD Webcam",
            "item_group": "Computer Accessories",
            "description": "Full HD webcam with built-in microphone",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "USB-HUB-4PORT",
            "item_name": "USB 3.0 Hub - 4 Port",
            "item_group": "Computer Accessories",
            "description": "Powered USB 3.0 hub with 4 ports",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "LAPTOP-STAND",
            "item_name": "Adjustable Laptop Stand",
            "item_group": "Computer Accessories",
            "description": "Aluminum adjustable laptop cooling stand",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "EXT-CABLE-HDMI",
            "item_name": "HDMI Extension Cable - 2m",
            "item_group": "Computer Accessories",
            "description": "High-speed HDMI extension cable, 2 meters",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },

        # Network Equipment
        {
            "item_code": "LAN-CAT6-5M",
            "item_name": "CAT6 LAN Cable - 5m",
            "item_group": "Network Equipment",
            "description": "CAT6 Ethernet patch cable, 5 meters",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "LAN-CAT6-10M",
            "item_name": "CAT6 LAN Cable - 10m",
            "item_group": "Network Equipment",
            "description": "CAT6 Ethernet patch cable, 10 meters",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "SWITCH-5PORT",
            "item_name": "Network Switch - 5 Port",
            "item_group": "Network Equipment",
            "description": "5-port gigabit network switch",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "ROUTER-WIFI",
            "item_name": "Wireless Router",
            "item_group": "Network Equipment",
            "description": "Dual-band wireless router with 4 LAN ports",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "PATCH-PANEL-24",
            "item_name": "Patch Panel - 24 Port",
            "item_group": "Network Equipment",
            "description": "24-port CAT6 patch panel",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },

        # Software Licenses
        {
            "item_code": "LIC-OFFICE-365",
            "item_name": "Microsoft 365 Business License",
            "item_group": "Software Licenses",
            "description": "Annual Microsoft 365 Business Premium license",
            "stock_uom": "License",
            "is_stock_item": 0
        },
        {
            "item_code": "LIC-WINDOWS-11",
            "item_name": "Windows 11 Pro License",
            "item_group": "Software Licenses",
            "description": "Windows 11 Pro OEM license",
            "stock_uom": "License",
            "is_stock_item": 0
        },
        {
            "item_code": "LIC-ANTIVIRUS",
            "item_name": "Antivirus Business License",
            "item_group": "Software Licenses",
            "description": "Annual antivirus business license per device",
            "stock_uom": "License",
            "is_stock_item": 0
        },
        {
            "item_code": "LIC-TEAM",
            "item_name": "Microsoft Teams License",
            "item_group": "Software Licenses",
            "description": "Annual Microsoft Teams business license",
            "stock_uom": "License",
            "is_stock_item": 0
        },

        # Training Materials
        {
            "item_code": "MANUAL-TRAINING",
            "item_name": "Training Manual - General",
            "item_group": "Training Materials",
            "description": "Generic training manual binder",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "CERT-BLANK",
            "item_name": "Training Certificate - Blank",
            "item_group": "Training Materials",
            "description": "Blank training certificate, premium paper",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "ID-CARD-HOLDER",
            "item_name": "ID Card Holder",
            "item_group": "Training Materials",
            "description": "PVC ID card holder with lanyard",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "TRAINING-KIT",
            "item_name": "Training Starter Kit",
            "item_group": "Training Materials",
            "description": "Complete training kit: pen, notebook, manual, certificate",
            "stock_uom": "Kit",
            "is_stock_item": 1
        },

        # Safety Equipment
        {
            "item_code": "FIRE-EXT-1KG",
            "item_name": "Fire Extinguisher - 1kg",
            "item_group": "Safety Equipment",
            "description": "1kg ABC dry powder fire extinguisher",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "FIRST-AID-KIT",
            "item_name": "First Aid Kit",
            "item_group": "Safety Equipment",
            "description": "Office first aid kit (50 person)",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
        {
            "item_code": "SAFETY-VEST",
            "item_name": "High Visibility Safety Vest",
            "item_group": "Safety Equipment",
            "description": "Reflective safety vest, size L",
            "stock_uom": "Nos",
            "is_stock_item": 1
        },
    ]

    return items

def create_item(item_data, warehouse, company):
    """Create a single item"""

    company_abbr = frappe.get_value("Company", company, "abbr")

    item = frappe.get_doc({
        "doctype": "Item",
        "item_code": item_data['item_code'],
        "item_name": item_data['item_name'],
        "item_group": item_data['item_group'],
        "description": item_data.get('description', ''),
        "stock_uom": item_data['stock_uom'],
        "is_stock_item": item_data['is_stock_item'],
        "include_item_in_manufacturing": 0,
        "default_warehouse": warehouse if item_data['is_stock_item'] else None,
        "item_defaults": [
            {
                "company": company,
                "default_warehouse": warehouse if item_data['is_stock_item'] else None,
                "expense_account": f"Cost of Goods Sold - {company_abbr}",
                "income_account": f"Sales - {company_abbr}",
                "buying_cost_center": f"Main - {company_abbr}",
                "selling_cost_center": f"Main - {company_abbr}"
            }
        ]
    }).insert()

    return item

def add_stock_to_item(item_code, warehouse, company, qty=50):
    """Add stock to item via stock entry"""

    try:
        stock_entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "items": [{
                "item_code": item_code,
                "qty": qty,
                "to_warehouse": warehouse,
                "uom": frappe.get_value("Item", item_code, "stock_uom")
            }],
            "company": company
        })
        stock_entry.submit()
    except Exception as e:
        print(f"  Note: Could not add stock to {item_code}: {e}")

def create_price_list(company):
    """Create price list for company"""

    price_list_name = f"{company} - Price List"

    if frappe.db.exists("Price List", price_list_name):
        return price_list_name

    price_list = frappe.get_doc({
        "doctype": "Price List",
        "price_list_name": price_list_name,
        "currency": "NGN",
        "enabled": 1,
        "selling": 1
    }).insert()

    return price_list.name

def get_default_rate(item_code):
    """Get default rate for item based on type"""

    # Default rates in NGN
    rates = {
        # Office Supplies
        "A4-PAPER-REAM": 4500,
        "A4-PAPER-BOX": 42000,
        "PEN-BLUE": 1500,
        "PEN-RED": 1500,
        "NOTEBOOK-A4": 3500,
        "ENVELOPE-DL": 8500,
        "STAPLER": 4500,
        "FILE-FOLDER": 4000,
        "MARKER-BLACK": 2500,
        "CALCULATOR": 8500,

        # Computer Accessories
        "MOUSE-WIRELESS": 8500,
        "KEYBOARD-USB": 9500,
        "HEADSET-USB": 18000,
        "WEBCAM-1080P": 25000,
        "USB-HUB-4PORT": 7500,
        "LAPTOP-STAND": 12000,
        "EXT-CABLE-HDMI": 4500,

        # Network Equipment
        "LAN-CAT6-5M": 3500,
        "LAN-CAT6-10M": 5500,
        "SWITCH-5PORT": 15000,
        "ROUTER-WIFI": 35000,
        "PATCH-PANEL-24": 45000,

        # Software Licenses
        "LIC-OFFICE-365": 45000,
        "LIC-WINDOWS-11": 65000,
        "LIC-ANTIVIRUS": 12000,
        "LIC-TEAM": 25000,

        # Training Materials
        "MANUAL-TRAINING": 2500,
        "CERT-BLANK": 1500,
        "ID-CARD-HOLDER": 2500,
        "TRAINING-KIT": 10000,

        # Safety Equipment
        "FIRE-EXT-1KG": 8500,
        "FIRST-AID-KIT": 15000,
        "SAFETY-VEST": 4500,
    }

    return rates.get(item_code, 5000)  # Default 5000 if not found

def create_item_price(item_code, price_list, rate):
    """Create item price"""

    try:
        item_price = frappe.get_doc({
            "doctype": "Item Price",
            "price_list": price_list,
            "item_code": item_code,
            "price_list_rate": rate
        }).insert()
    except Exception as e:
        print(f"  Note: Could not set price for {item_code}: {e}")

def cleanup_lassod_items():
    """Clean up all Lassod items and data"""

    company = "Lassod Consulting Limited"
    print(f"\n{'='*60}")
    print(f"Cleaning up {company} items")
    print(f"{'='*60}\n")

    items = get_lassod_items()

    for item_data in items:
        item_code = item_data['item_code']

        # Delete item prices
        item_prices = frappe.get_all("Item Price",
            filters={"item_code": item_code},
            pluck="name"
        )

        for price_name in item_prices:
            frappe.delete_doc("Item Price", price_name)
            print(f"✓ Deleted item price: {price_name}")

        # Delete item
        if frappe.db.exists("Item", item_code):
            try:
                frappe.delete_doc("Item", item_code)
                print(f"✓ Deleted item: {item_code}")
            except Exception as e:
                print(f"✗ Could not delete {item_code}: {e}")

    # Delete item groups
    groups = ["Office Supplies", "Computer Accessories", "Network Equipment",
              "Software Licenses", "Training Materials", "Safety Equipment"]

    for group in groups:
        if frappe.db.exists("Item Group", group):
            try:
                frappe.delete_doc("Item Group", group)
                print(f"✓ Deleted item group: {group}")
            except Exception as e:
                print(f"✗ Could not delete {group}: {e}")

    print(f"\n✅ Cleanup complete!")

def list_lassod_items():
    """List all Lassod items"""

    items = get_lassod_items()
    item_codes = [item['item_code'] for item in items]

    existing_items = frappe.get_all("Item",
        filters={"item_code": ["in", item_codes]},
        fields=["item_code", "item_name", "item_group", "stock_uom", "is_stock_item"],
        order_by="item_code"
    )

    print(f"\n{'='*60}")
    print(f"Lassod Consulting Limited - Items List")
    print(f"{'='*60}\n")

    if not existing_items:
        print("No items found. Run create_lassod_items() first.\n")
        return

    print(f"{'Item Code':<20} {'Item Name':<30} {'Group':<20} {'UoM':<10} {'Stock':<5}")
    print("-" * 90)

    for item in existing_items:
        stock_status = "Yes" if item.is_stock_item else "No"
        print(f"{item.item_code:<20} {item.item_name:<30} {item.item_group:<20} {item.stock_uom:<10} {stock_status:<5}")

    print(f"\nTotal: {len(existing_items)} items\n")

# Main execution
if __name__ == "__main__":
    print("""
Lassod Consulting Limited - Item Management
===========================================

Usage:
1. bench --site lassod console
2. execfile('./apps/posawesome/create_lassod_items.py')
3. Choose one of the following:

Options:
- create_lassod_items()       : Create all items for Lassod Consulting
- cleanup_lassod_items()      : Delete all Lassod items
- list_lassod_items()         : List existing Lassod items

Example:
>>> execfile('./apps/posawesome/create_lassod_items.py')
>>> create_lassod_items()
""")

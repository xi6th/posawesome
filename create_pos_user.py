#!/usr/bin/env python3
"""
Create POS User with Profile and Company Assignment
Run in bench console: bench --site [site] console
>>> execfile('./apps/posawesome/create_pos_user.py')
"""

import frappe

def create_pos_user(email, first_name, last_name, company, pos_profile=None, role="Cashier"):
    """
    Create a new POS user with profile and company assignment

    Args:
        email: User email address
        first_name: User's first name
        last_name: User's last name
        company: Company name to assign
        pos_profile: POS Profile name (optional)
        role: Role to assign (default: Cashier)

    Returns:
        Created user document
    """

    # Check if user already exists
    if frappe.db.exists("User", email):
        print(f"⚠ User {email} already exists. Updating...")
        user = frappe.get_doc("User", email)
    else:
        print(f"Creating new user: {email}")
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "send_welcome_email": 0,
            "enabled": 1
        })

    # Add role if not exists
    role_exists = False
    for user_role in user.get("roles", []):
        if user_role.get("role") == role:
            role_exists = True
            break

    if not role_exists:
        user.append("roles", {"role": role})
        print(f"✓ Added role: {role}")

    # Save user
    user.save()
    print(f"✓ User saved: {user.name}")

    # Assign company to user (via Employee or User Permission)
    assign_company_to_user(user.name, company)

    # Assign POS profile if provided
    if pos_profile:
        assign_pos_profile_to_user(user.name, pos_profile, company)
    else:
        print(f"ℹ No POS profile assigned. User will need to select profile manually.")

    # Set default company in user preferences
    set_user_default_company(user.name, company)

    return user

def assign_company_to_user(user_email, company):
    """Assign company to user via User Permission"""

    # Check if User Permission already exists
    existing_permission = frappe.db.exists("User Permission", {
        "user": user_email,
        "allow": "Company",
        "for_value": company
    })

    if existing_permission:
        print(f"✓ Company permission already exists: {company}")
        return

    # Create User Permission for Company
    try:
        user_permission = frappe.get_doc({
            "doctype": "User Permission",
            "user": user_email,
            "allow": "Company",
            "for_value": company,
            "is_default": 1
        })
        user_permission.insert()
        print(f"✓ Assigned company: {company}")
    except Exception as e:
        print(f"⚠ Could not assign company via User Permission: {e}")
        print(f"  User may still have access based on their role")

def assign_pos_profile_to_user(user_email, pos_profile, company):
    """Assign POS profile to user"""

    # Check if profile exists
    if not frappe.db.exists("POS Profile", pos_profile):
        print(f"✗ POS Profile '{pos_profile}' not found")
        return

    # Check if assignment already exists
    existing = frappe.db.exists("POS Profile User", {
        "user": user_email,
        "parent": pos_profile
    })

    if existing:
        print(f"✓ POS profile already assigned: {pos_profile}")
        return

    # Add user to POS Profile
    try:
        profile_doc = frappe.get_doc("POS Profile", pos_profile)
        profile_doc.append("users", {"user": user_email})
        profile_doc.save()
        print(f"✓ Assigned POS profile: {pos_profile}")
    except Exception as e:
        print(f"⚠ Could not assign POS profile: {e}")

def set_user_default_company(user_email, company):
    """Set default company in user settings"""

    try:
        # Check if company exists
        if not frappe.db.exists("Company", company):
            print(f"⚠ Company '{company}' not found, skipping default company setting")
            return

        # Set user preference via System Settings (simplified approach)
        from frappe.utils import set_default

        # Set default company for the user session
        set_default("company", company, user_email)
        print(f"✓ Set default company: {company}")
    except Exception as e:
        print(f"⚠ Could not set default company: {e}")

def list_pos_users():
    """List all users with POS-related roles"""
    pos_roles = ["Cashier", "Accounts Manager", "Sales Manager", "Sales User"]

    users = frappe.get_all("User",
        filters={
            "enabled": 1,
            "has_role": ["in", pos_roles]
        },
        fields=["email", "first_name", "last_name"],
        distinct=True
    )

    print("\n📋 Current POS Users:")
    print("-" * 50)
    for user in users:
        print(f"  • {user.email} ({user.first_name} {user.last_name})")

def list_available_profiles():
    """List available POS profiles"""
    profiles = frappe.get_all("POS Profile",
        fields=["name", "company", "warehouse"],
        order_by="name"
    )

    print("\n📋 Available POS Profiles:")
    print("-" * 50)
    for profile in profiles:
        print(f"  • {profile.name}")
        print(f"    Company: {profile.company}")
        print(f"    Warehouse: {profile.warehouse}")

def list_available_companies():
    """List available companies"""
    companies = frappe.get_all("Company",
        fields=["name", "abbr", "country"],
        order_by="name"
    )

    print("\n📋 Available Companies:")
    print("-" * 50)
    for company in companies:
        print(f"  • {company.name} ({company.abbr}) - {company.country}")

# Example usage functions
def create_sample_users():
    """Create sample POS users for testing"""

    print("\n" + "="*50)
    print("Creating Sample POS Users")
    print("="*50 + "\n")

    # Get first available company and profile
    companies = frappe.get_all("Company", pluck="name", limit=1)
    if not companies:
        print("✗ No companies found. Please create a company first.")
        return

    company = companies[0]

    profiles = frappe.get_all("POS Profile", pluck="name", limit=1)
    pos_profile = profiles[0] if profiles else None

    if not pos_profile:
        print("⚠ No POS Profile found. User will need profile assignment later.")
        pos_profile = None

    # Create Cashier
    print("\n1. Creating Cashier:")
    create_pos_user(
        email="john.cashier@example.com",
        first_name="John",
        last_name="Cashier",
        company=company,
        pos_profile=pos_profile,
        role="Cashier"
    )

    # Create Supervisor
    print("\n2. Creating Supervisor:")
    create_pos_user(
        email="mary.supervisor@example.com",
        first_name="Mary",
        last_name="Supervisor",
        company=company,
        pos_profile=pos_profile,
        role="Accounts Manager"
    )

    # Create Sales Manager
    print("\n3. Creating Sales Manager:")
    create_pos_user(
        email="bob.manager@example.com",
        first_name="Bob",
        last_name="Manager",
        company=company,
        pos_profile=pos_profile,
        role="Sales Manager"
    )

    print("\n✅ Sample users created successfully!")
    print(f"\nCompany used: {company}")
    if pos_profile:
        print(f"POS Profile used: {pos_profile}")
    print("\nUsers can now login and access POS with their credentials.")

# Interactive wizard
def interactive_user_creation():
    """Interactive user creation wizard"""
    print("\n" + "="*50)
    print("POS User Creation Wizard")
    print("="*50 + "\n")

    # List available data
    list_available_companies()
    list_available_profiles()

    print("\n" + "-"*50)
    print("Enter user details:")
    print("-"*50)

    email = input("Email: ").strip()
    if not email:
        print("✗ Email is required")
        return

    first_name = input("First Name: ").strip()
    if not first_name:
        print("✗ First name is required")
        return

    last_name = input("Last Name: ").strip()
    if not last_name:
        print("✗ Last name is required")
        return

    company = input("Company (press Enter for default): ").strip()
    if not company:
        companies = frappe.get_all("Company", pluck="name", limit=1)
        if companies:
            company = companies[0]
        else:
            print("✗ No company found")
            return

    pos_profile = input("POS Profile (press Enter to skip): ").strip()
    if not pos_profile:
        pos_profile = None

    role = input("Role [Cashier]: ").strip()
    if not role:
        role = "Cashier"

    print("\n" + "-"*50)
    print("Creating user...")
    print("-"*50 + "\n")

    user = create_pos_user(email, first_name, last_name, company, pos_profile, role)

    print("\n✅ User created successfully!")
    print(f"\nLogin URL: http://your-site.com/app")
    print(f"Email: {email}")
    print(f"Note: User will need to set password on first login")

if __name__ == "__main__":
    import sys

    print("""
POS User Creation Tool
======================

Usage:
1. bench --site [site] console
2. execfile('./apps/posawesome/create_pos_user.py')
3. Choose one of the following:

Options:
- create_sample_users()      : Create 3 sample users (Cashier, Supervisor, Manager)
- interactive_user_creation(): Interactive wizard to create custom user
- list_pos_users()           : List all existing POS users
- list_available_profiles()  : List available POS profiles
- list_available_companies() : List available companies

Example:
>>> execfile('./apps/posawesome/create_pos_user.py')
>>> create_sample_users()
""")

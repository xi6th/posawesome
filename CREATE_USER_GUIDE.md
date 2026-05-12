# POS User Creation Guide

Quick guide to creating POS users with profile and company assignments.

## 🚀 Quick Start

### Method 1: Create Sample Users (Fastest)

```bash
bench --site [your-site] console
>>> execfile('./apps/posawesome/create_pos_user.py')
>>> create_sample_users()
```

This creates 3 users automatically:
- **john.cashier@example.com** (Cashier)
- **mary.supervisor@example.com** (Accounts Manager)
- **bob.manager@example.com** (Sales Manager)

### Method 2: Interactive Wizard

```bash
bench --site [your-site] console
>>> execfile('./apps/posawesome/create_pos_user.py')
>>> interactive_user_creation()
```

Follow the prompts to create a custom user.

### Method 3: Programmatic Creation

```python
# In bench console
>>> execfile('./apps/posawesome/create_pos_user.py')

# Create single user
>>> create_pos_user(
...     email="user@example.com",
...     first_name="Jane",
...     last_name="Doe",
...     company="Your Company Name",
...     pos_profile="Your POS Profile",
...     role="Cashier"
... )
```

## 📋 Available Commands

### Information Commands
```python
# List all POS users
>>> list_pos_users()

# List available POS profiles
>>> list_available_profiles()

# List available companies
>>> list_available_companies()
```

### User Creation Commands
```python
# Create sample users
>>> create_sample_users()

# Interactive wizard
>>> interactive_user_creation()

# Manual creation
>>> create_pos_user(email, first_name, last_name, company, pos_profile, role)
```

## 👤 User Roles

Common POS roles:
- **Cashier** - Basic POS operations
- **Accounts Manager** - Supervisor with financial permissions
- **Sales Manager** - Sales oversight
- **Sales User** - Basic sales operations

## 🔧 What the Script Does

1. **Creates User** - Adds new user to system
2. **Assigns Role** - Gives appropriate permissions
3. **Assigns Company** - Links user to company via User Permission
4. **Assigns POS Profile** - Links user to specific POS profile
5. **Sets Defaults** - Configures default company for user

## ⚙️ Parameters Explained

```python
create_pos_user(
    email="user@example.com",      # Required: Login email
    first_name="John",              # Required: First name
    last_name="Doe",                # Required: Last name
    company="My Company",           # Required: Company name
    pos_profile="Main POS",         # Optional: POS profile name
    role="Cashier"                  # Optional: Role (default: Cashier)
)
```

## 🔐 First Login

After creating a user:
1. Navigate to `/app/login` in browser
2. Enter email address
3. System will prompt to set password on first login
4. User can then access POS at `/app/pos`

## ✅ Verification

### Check User Exists
```python
# Check if user was created
>>> frappe.db.exists("User", "john.cashier@example.com")

# Get user details
>>> user = frappe.get_doc("User", "john.cashier@example.com")
>>> print(f"Name: {user.full_name}")
>>> print(f"Enabled: {user.enabled}")
>>> print(f"Roles: {[r.role for r in user.roles]}")
```

### Check Permissions
```python
# Check company permission
>>> frappe.db.exists("User Permission", {
...     "user": "john.cashier@example.com",
...     "allow": "Company",
...     "for_value": "Your Company"
... })

# Check POS profile assignment
>>> profile = frappe.get_doc("POS Profile", "Your POS Profile")
>>> print([u.user for u in profile.users])
```

## 🛠️ Troubleshooting

### "User already exists"
The script will update the existing user instead of creating a duplicate.

### "Company not found"
```python
# List available companies
>>> list_available_companies()

# Use exact company name from the list
```

### "POS Profile not found"
```python
# List available profiles
>>> list_available_profiles()

# Create profile first or leave pos_profile=None
```

### Permission errors
- Ensure you're logged in as Administrator
- Check that user has necessary permissions to create users

## 🔄 Modifying Existing Users

```python
# Get existing user
>>> user = frappe.get_doc("User", "john.cashier@example.com")

# Add additional role
>>> user.append("roles", {"role": "Sales User"})
>>> user.save()

# Remove role
>>> for role in user.roles:
...     if role.role == "Cashier":
...         user.roles.remove(role)
>>> user.save()
```

## 🗑️ Deleting Users

⚠️ **Caution**: This cannot be undone

```python
# Revoke all permissions first
>>> frappe.db.delete("User Permission", {"user": "john.cashier@example.com"})

# Delete user
>>> frappe.delete_doc("User", "john.cashier@example.com")
```

## 📊 Example: Complete Setup

```python
# 1. List available resources
>>> list_available_companies()
>>> list_available_profiles()

# 2. Create a cashier for "Main Store"
>>> create_pos_user(
...     email="store1.cashier@example.com",
...     first_name="Alice",
...     last_name="Cashier",
...     company="My Company",
...     pos_profile="Main Store POS",
...     role="Cashier"
... )

# 3. Create a supervisor
>>> create_pos_user(
...     email="store1.manager@example.com",
...     first_name="Bob",
...     last_name="Manager",
...     company="My Company",
...     pos_profile="Main Store POS",
...     role="Accounts Manager"
... )

# 4. Verify users
>>> list_pos_users()
```

## 🔗 Related Files

- **test_data_generator.py** - Creates test data including users
- **test_data_cheatsheet.md** - User testing examples
- **TEST_DATA_GUIDE.md** - Complete test data documentation

## 💡 Tips

1. **Use descriptive emails** - `store1.cashier@example.com` vs `user1@example.com`
2. **Assign appropriate roles** - Not all users need supervisor permissions
3. **Test first login** - Verify users can access POS with their credentials
4. **Keep it simple** - Start with sample users, then customize
5. **Document access** - Keep track of who has which permissions

## 📖 Next Steps

After creating users:
1. **Test login** - Verify users can log in
2. **Assign passwords** - Users set passwords on first login
3. **Configure POS** - Check profile assignments
4. **Train users** - Provide POS training
5. **Monitor access** - Review user activity regularly

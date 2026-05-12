#!/bin/bash
# Stock Confidence Troubleshooting Script
# Helps diagnose and fix "Stock Confidence Offline" warning

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ $1${NC}"; }
print_header() { echo -e "${BLUE}▶ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BENCH_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Change to bench directory
cd "$BENCH_DIR" || exit 1

echo ""
echo "===================================================="
echo "  Stock Confidence Offline - Troubleshooting Tool"
echo "===================================================="
echo ""

# Get site
SITES=($(bench site list 2>/dev/null | grep -v "^$")) || true

if [ ${#SITES[@]} -eq 0 ]; then
    print_error "No sites found"
    exit 1
elif [ ${#SITES[@]} -eq 1 ]; then
    SITE=${SITES[0]}
else
    PS3="Select site: "
    select SITE in "${SITES[@]}"; do
        [ -n "$SITE" ] && break
    done
fi

print_success "Selected site: $SITE"
echo ""

# Menu
echo "Choose an option:"
echo "1) Check stock status and diagnose issue"
echo "2) Add stock to Lassod items (fixes missing stock)"
echo "3) Clear all caches"
echo "4) Verify stock data exists"
echo "5) Show troubleshooting guide"
echo "6) Exit"
echo ""
read -p "Enter choice [1-6]: " CHOICE

case $CHOICE in
    1)
        print_header "Diagnosing stock confidence issue..."
        echo ""
        bench --site "$SITE" console --execute "
import frappe
from frappe.db import sql

print('\n' + '='*60)
print('Stock Confidence Diagnosis')
print('='*60)

# Check company
company = 'Lassod Consulting Limited'
if frappe.db.exists('Company', company):
    print(f'\n✓ Company exists: {company}')
else:
    print(f'\n✗ Company not found: {company}')
    print('  Run option 2 to create company and items')

# Check warehouse
warehouse = f\"Stores - {frappe.get_value('Company', company, 'abbr')}\"
if frappe.db.exists('Warehouse', warehouse):
    print(f'✓ Warehouse exists: {warehouse}')
else:
    print(f'✗ Warehouse not found: {warehouse}')

# Check items count
items = frappe.get_all('Item', filters={'is_stock_item': 1}, pluck='name')
print(f'\n✓ Stock items in system: {len(items)}')

# Check items with stock
stock_data = sql('''
    SELECT COUNT(DISTINCT item_code), SUM(actual_qty)
    FROM \`tabBin\`
    WHERE warehouse LIKE %s
''', f'%{frappe.get_value(\"Company\", company, \"abbr\")}%')

if stock_data and stock_data[0]:
    items_with_stock, total_qty = stock_data[0]
    print(f'✓ Items with stock: {items_with_stock or 0}')
    print(f'✓ Total quantity: {total_qty or 0}')

    if items_with_stock == 0:
        print('\n⚠ No stock found! This is causing the warning.')
        print('  Run option 2 to add stock to items.')
    else:
        print(f'\n✓ Stock data looks good!')
        print(f'  If warning persists, try option 3 (Clear caches)')
else:
    print('✗ Could not check stock data')

# Check if stock cache ready flag exists (from offline sync)
print(f'\n⚠ If warning persists after stock exists:')
print(f'  1. Open POS in browser')
print(f'  2. Go to Status > Clear Cache')
print(f'  3. Reload page (Ctrl+R)')
print(f'  4. Wait for sync to complete')

print('\n' + '='*60)
"
        ;;
    2)
        print_header "Adding stock to Lassod items..."
        echo ""
        bench --site "$SITE" console --execute "execfile('$SCRIPT_DIR/create_lassod_items.py'); create_lassod_items()"
        echo ""
        print_success "Stock added to Lassod items!"
        print_info "Next: Clear browser cache and reload POS"
        ;;
    3)
        print_header "Clearing all caches..."
        echo ""
        bench --site "$SITE" clear-cache
        print_success "Server cache cleared!"
        echo ""
        print_info "Now clear browser cache:"
        echo "  1. Open POS in browser (F12 for DevTools)"
        echo "  2. Go to Application tab > Clear site data"
        echo "  3. Reload page (Ctrl+R)"
        ;;
    4)
        print_header "Verifying stock data..."
        echo ""
        bench --site "$SITE" console --execute "
import frappe
from frappe.db import sql

company = 'Lassod Consulting Limited'
abbr = frappe.get_value('Company', company, 'abbr')

print('\n' + '='*60)
print('Stock Data Verification')
print('='*60 + '\n')

# Show items without stock
items_without_stock = sql('''
    SELECT i.item_code, i.item_name
    FROM tabItem i
    LEFT JOIN tabBin b ON i.item_code = b.item_code
    WHERE i.is_stock_item = 1
    AND i.item_code LIKE 'A4-%' OR i.item_code LIKE 'PEN-%'
    AND b.item_code IS NULL
    LIMIT 10
''')

if items_without_stock:
    print('Items without stock (first 10):')
    for item in items_without_stock:
        print(f'  • {item[0]} - {item[1]}')
else:
    print('✓ All checked items have stock!')

# Show stock summary
stock_summary = sql('''
    SELECT item_code, warehouse, actual_qty
    FROM tabBin
    WHERE warehouse LIKE %s
    ORDER BY actual_qty DESC
    LIMIT 10
''', f'%{abbr}%')

if stock_summary:
    print(f'\nStock levels (top 10):')
    for item, warehouse, qty in stock_summary:
        print(f'  • {item}: {qty} in {warehouse}')

print('\n' + '='*60)
"
        ;;
    5)
        print_header "Stock Confidence Troubleshooting Guide"
        echo ""
        cat "$SCRIPT_DIR/fix_stock_confidence.md"
        ;;
    6)
        print_info "Exiting..."
        exit 0
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
print_info "Additional help: Check fix_stock_confidence.md for detailed guide"
echo ""

#!/bin/bash
# Lassod Consulting Limited - Stock Items Creation Script
# Quick script to create stock items for Lassod Consulting

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

# Check if bench exists
if ! command -v bench &> /dev/null; then
    print_error "Frappe bench not found"
    exit 1
fi

# Get available sites
SITES=($(bench site list 2>/dev/null | grep -v "^$")) || true

if [ ${#SITES[@]} -eq 0 ]; then
    print_error "No sites found"
    exit 1
fi

# Select site
if [ ${#SITES[@]} -eq 1 ]; then
    SITE=${SITES[0]}
    print_success "Found site: $SITE"
else
    echo ""
    print_info "Available sites:"
    PS3="Select a site (number): "
    select SITE in "${SITES[@]}"; do
        [ -n "$SITE" ] && break
    done
fi

echo ""
print_info "Target site: $SITE"
echo ""

# Show menu
echo "Lassod Consulting Limited - Stock Items Management"
echo "===================================================="
echo ""
echo "What would you like to do?"
echo "1) Create stock items for Lassod Consulting (40 items)"
echo "2) List existing Lassod items"
echo "3) Clean up all Lassod items"
echo "4) View item categories"
echo "5) Exit"
echo ""
read -p "Enter choice [1-5]: " CHOICE

case $CHOICE in
    1)
        echo ""
        print_header "Creating stock items for Lassod Consulting Limited..."
        echo ""
        bench --site "$SITE" console --execute "execfile('$SCRIPT_DIR/create_lassod_items.py'); create_lassod_items()"
        echo ""
        print_success "Stock items created successfully!"
        echo ""
        print_info "Summary:"
        echo "  • Company: Lassod Consulting Limited"
        echo "  • Items created: 40"
        echo "  • Categories: 6 (Office Supplies, Computer Accessories, etc.)"
        echo "  • Currency: NGN (₦)"
        echo "  • Stock added: 50 units per item"
        ;;
    2)
        echo ""
        print_header "Listing existing Lassod items..."
        echo ""
        bench --site "$SITE" console --execute "execfile('$SCRIPT_DIR/create_lassod_items.py'); list_lassod_items()"
        ;;
    3)
        echo ""
        print_header "Cleaning up all Lassod items..."
        echo ""
        read -p "Are you sure? This will delete all Lassod items. (yes/no): " CONFIRM
        if [ "$CONFIRM" = "yes" ]; then
            bench --site "$SITE" console --execute "execfile('$SCRIPT_DIR/create_lassod_items.py'); cleanup_lassod_items()"
            echo ""
            print_success "Cleanup complete!"
        else
            print_info "Cleanup cancelled"
        fi
        ;;
    4)
        echo ""
        print_header "Item Categories for Lassod Consulting"
        echo ""
        echo "📦 Office Supplies (10 items)"
        echo "   • A4 Paper (Ream & Box)"
        echo "   • Pens (Blue & Red)"
        echo "   • Notebooks, Envelopes, Staplers, etc."
        echo ""
        echo "💻 Computer Accessories (7 items)"
        echo "   • Mouse, Keyboard, Headset"
        echo "   • Webcam, USB Hub, Laptop Stand"
        echo ""
        echo "🌐 Network Equipment (5 items)"
        echo "   • LAN Cables, Switch, Router"
        echo "   • Patch Panel"
        echo ""
        echo "🔐 Software Licenses (4 items)"
        echo "   • Microsoft 365, Windows 11"
        echo "   • Antivirus, Teams"
        echo ""
        echo "📚 Training Materials (4 items)"
        echo "   • Manuals, Certificates"
        echo "   • ID Holders, Training Kits"
        echo ""
        echo "⚠️  Safety Equipment (3 items)"
        echo "   • Fire Extinguisher, First Aid Kit"
        echo "   • Safety Vest"
        echo ""
        echo "Total: 40 items across 6 categories"
        ;;
    5)
        print_info "Exiting..."
        exit 0
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
print_info "Next steps:"
echo "  1. Create POS profile: Check CREATE_USER_GUIDE.md"
echo "  2. Add POS users: Run create_user.sh"
echo "  3. Configure taxes: Set up Nigerian tax templates"
echo "  4. Test POS: Create test invoices"
echo "  5. Read docs: Check LASSOD_ITEMS_GUIDE.md for details"
echo ""

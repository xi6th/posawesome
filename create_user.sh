#!/bin/bash
# POS User Creation Wrapper Script
# Quick script to create POS users from command line

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
else
    echo ""
    print_info "Available sites:"
    PS3="Select a site (number): "
    select SITE in "${SITES[@]}"; do
        [ -n "$SITE" ] && break
    done
fi

print_success "Selected site: $SITE"
echo ""

# Show menu
echo "POS User Creation Menu"
echo "====================="
echo "1) Create sample users (Cashier, Supervisor, Manager)"
echo "2) Create custom user (interactive wizard)"
echo "3) List existing POS users"
echo "4) List available POS profiles"
echo "5) List available companies"
echo "6) Exit"
echo ""
read -p "Enter choice [1-6]: " CHOICE

case $CHOICE in
    1)
        print_header "Creating sample POS users..."
        bench --site "$SITE" console --execute "execfile('$SCRIPT_DIR/create_pos_user.py'); create_sample_users()"
        print_success "Sample users created!"
        ;;
    2)
        print_header "Launching interactive user creation wizard..."
        bench --site "$SITE" console --execute "execfile('$SCRIPT_DIR/create_pos_user.py'); interactive_user_creation()"
        ;;
    3)
        print_header "Listing POS users..."
        bench --site "$SITE" console --execute "execfile('$SCRIPT_DIR/create_pos_user.py'); list_pos_users()"
        ;;
    4)
        print_header "Listing available POS profiles..."
        bench --site "$SITE" console --execute "execfile('$SCRIPT_DIR/create_pos_user.py'); list_available_profiles()"
        ;;
    5)
        print_header "Listing available companies..."
        bench --site "$SITE" console --execute "execfile('$SCRIPT_DIR/create_pos_user.py'); list_available_companies()"
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
print_info "Next steps:"
echo "  1. Start bench: bench start"
echo "  2. Login at: http://$SITE/app/login"
echo "  3. Access POS at: http://$SITE/app/pos"
echo "  4. Check CREATE_USER_GUIDE.md for more details"
echo ""

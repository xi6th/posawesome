#!/bin/bash
# POSAwesome Test Data Generator Wrapper
# Quick script to generate test data from command line

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if bench is in PATH
if ! command -v bench &> /dev/null; then
    print_error "Frappe bench not found in PATH"
    print_info "Please source bench environment or run from within a bench session"
    exit 1
fi

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BENCH_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Change to bench directory
cd "$BENCH_DIR" || exit 1

# Check if sites exist
SITES=($(bench site list 2>/dev/null | grep -v "^$")) || true

if [ ${#SITES[@]} -eq 0 ]; then
    print_error "No sites found in this bench"
    print_info "Create a site first: bench new-site mysite.local"
    exit 1
fi

# Prompt for site selection
if [ ${#SITES[@]} -eq 1 ]; then
    SITE=${SITES[0]}
    print_success "Found site: $SITE"
else
    echo ""
    print_info "Select a site:"
    select SITE in "${SITES[@]}"; do
        if [ -n "$SITE" ]; then
            break
        fi
    done
fi

# Check if site exists
if ! bench --site "$SITE" exists &> /dev/null; then
    print_error "Site $SITE does not exist"
    exit 1
fi

# Ask what to do
echo ""
echo "What would you like to do?"
echo "1) Generate test data"
echo "2) Clean up test data"
echo "3) Re-generate test data (cleanup + generate)"
echo "4) Exit"
read -p "Enter choice [1-4]: " CHOICE

case $CHOICE in
    1)
        print_info "Generating test data for $SITE..."
        bench --site "$SITE" console --execute "execfile('$SCRIPT_DIR/test_data_generator.py'); create_test_data()"
        print_success "Test data generation complete!"
        ;;
    2)
        print_info "Cleaning up test data from $SITE..."
        bench --site "$SITE" console --execute "execfile('$SCRIPT_DIR/test_data_generator.py'); cleanup_test_data()"
        print_success "Test data cleanup complete!"
        ;;
    3)
        print_info "Re-generating test data for $SITE..."
        bench --site "$SITE" console --execute "execfile('$SCRIPT_DIR/test_data_generator.py'); cleanup_test_data(); create_test_data()"
        print_success "Test data re-generation complete!"
        ;;
    4)
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
echo "  1. Start the bench: bench start"
echo "  2. Open POS in browser: http://$SITE/app/pos"
echo "  3. Login with: pos_cashier@test.com or pos_manager@test.com"
echo "  4. Check TEST_DATA_GUIDE.md for more information"
echo ""

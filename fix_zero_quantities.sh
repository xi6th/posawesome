#!/bin/bash
# Fix Zero Quantities in POS - Quick Guide

echo "================================================"
echo "  Fix: POS Items Showing Zero Quantities"
echo "================================================"
echo ""

echo "🔍 THE PROBLEM:"
echo "Your POS is showing items but with 0 quantity because:"
echo "  • Items exist in database ✓"
echo "  • Stock exists in database ✓"
echo "  • BUT POS offline cache hasn't synced ✗"
echo ""

echo "🔧 THE SOLUTION:"
echo ""

echo "Step 1: Connect to Server"
echo "  • Make sure you have internet connection"
echo "  • POS can reach the Frappe server"
echo ""

echo "Step 2: Clear POS Cache"
echo "  • Open POS in browser"
echo "  • Click 'Status' menu (top right)"
echo "  • Click 'Clear Cache'"
echo "  • Wait for cache to clear"
echo ""

echo "Step 3: Force Stock Sync"
echo "  • In POS, go to Status menu"
echo "  • Click 'Sync Now' or 'Refresh Offline Data'"
echo "  • Wait for sync to complete (watch progress bar)"
echo ""

echo "Step 4: Reload POS"
echo "  • Press Ctrl+R (or F5) to reload"
echo "  • Wait for POS to fully load"
echo "  • Stock quantities should now appear!"
echo ""

echo "Step 5: If Still Zero - Try Browser Cache Clear"
echo "  • Press F12 (Developer Tools)"
echo "  • Go to Application tab"
echo "  • Click 'Clear site data'"
echo "  • Close and reopen POS"
echo ""

echo "⚠️  IMPORTANT:"
echo "The 'Stock Confidence Offline' warning means your POS is"
echo "operating in offline mode and needs to sync stock data from"
echo "the server before it can show accurate quantities."
echo ""

echo "✅ VERIFICATION:"
echo "After syncing, you should see:"
echo "  • T-shirt: 100 units"
echo "  • Laptop: 100 units"
echo "  • Book: 100 units"
echo "  • etc."
echo ""

echo "If this doesn't work, run:"
echo "  ./fix_stock_confidence.sh"
echo ""

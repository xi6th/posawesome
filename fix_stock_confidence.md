# Fix "Stock Confidence Offline" Warning

## 🔍 Understanding the Issue

The "Stock Confidence Offline" warning appears when:
- POSAwesome is operating in offline mode
- Stock cache hasn't been initialized or synced
- The `stock_cache_ready` prerequisite is missing

**Default Policy**: `require_manager_override` - Requires supervisor approval before selling items with uncertain stock levels.

## ✅ Solutions (In Order of Preference)

### Solution 1: Refresh Stock Data (Recommended)

**When to use**: When you have internet connection

1. **Connect to the internet** and ensure POS can reach the server
2. **Open POS** and let it fully load
3. **Wait for sync** - Let POS complete all background syncs
4. **Refresh items**:
   - Go to **Status** menu
   - Click **Sync Now** or **Refresh Offline Data**
   - Wait for stock sync to complete

**What this does**: Fetches current stock levels from server and populates local cache

### Solution 2: Clear Cache and Reload

**When to use**: When sync seems stuck or cache is corrupted

1. **Open POS** and go to **Status** menu
2. Click **Clear Cache**
3. **Wait** for cache to clear completely
4. **Reload** the POS page (Ctrl+R or F5)
5. **Wait** for initial sync to complete

**What this does**: Clears corrupted cache and rebuilds it from scratch

### Solution 3: Check Stock Data Exists

**When to use**: When warning persists after clearing cache

**In Bench Console**:
```python
bench --site [your-site] console

# Check if items have stock entries
from frappe.db import sql

# Count items with stock
items_with_stock = sql("""
    SELECT COUNT(DISTINCT item_code)
    FROM `tabBin`
    WHERE actual_qty > 0
""")

print(f"Items with stock: {items_with_stock[0][0]}")

# Check specific item
item_stock = sql("""
    SELECT item_code, warehouse, actual_qty
    FROM `tabBin`
    WHERE item_code = 'YOUR-ITEM-CODE'
    LIMIT 5
""")

for stock in item_stock:
    print(f"{stock[0]}: {stock[2]} in {stock[1]}")
```

**If no stock exists**:
```python
# Add stock to items using the script
execfile('./apps/posawesome/create_lassod_items.py')
add_stock_to_item("A4-PAPER-REAM", "Stores - LCL",
                 "Lassod Consulting Limited", qty=50)
```

### Solution 4: Adjust Offline Policy (Temporary)

**When to use**: When you need to operate offline immediately

**Option A**: Change to Warning Only
```python
# In bench console
from frappe.db import set_value

# This changes policy to show warning but allow sales
# You'll need to set this in POS Profile or system settings
```

**Option B**: Use Supervisor PIN
- The system is asking for supervisor approval
- Have a supervisor enter their PIN
- This allows the sale to proceed despite low stock confidence

### Solution 5: Force Stock Cache Initialization

**When to use**: Technical solution when other methods fail

1. **Open Browser Developer Tools** (F12)
2. **Go to Console** tab
3. **Run this command**:
```javascript
// Check stock cache status
console.log('Stock ready:', frappe.boot.stock_cache_ready);
console.log('Local stock cache:', localStorage.getItem('local_stock_cache'));

// Force stock cache refresh (if items are loaded)
if (window.posapp && window.posapp.$store) {
  console.log('POS Store State:', window.posapp.$store.state);
}
```

4. **Reload POS** after checking

## 🔧 Permanent Fixes

### Fix 1: Ensure Stock Exists for All Items

```python
bench --site [site] console

# Get all items without stock
from frappe.db import sql

items_without_stock = sql("""
    SELECT i.item_code, i.item_name
    FROM `tabItem` i
    LEFT JOIN `tabBin` b ON i.item_code = b.item_code
    WHERE i.is_stock_item = 1
    AND b.item_code IS NULL
    LIMIT 20
""")

print("Items without stock:")
for item in items_without_stock:
    print(f"  {item[0]} - {item[1]}")

# Add stock using your create script
execfile('./apps/posawesome/create_lassod_items.py')

# Or manually add stock
from posawesome.posawesome.api.invoice_processing.stock import add_stock_to_item
add_stock_to_item("ITEM-CODE", "Stores - LCL", "Lassod Consulting Limited", qty=50)
```

### Fix 2: Configure Offline Policy

The default policy is `require_manager_override`. You can change this:

**In POS Profile**:
1. Go to **POS Profile** in Desk
2. Open your POS profile (e.g., "Lassod POS")
3. Look for **Offline Policy** settings
4. Change **Stock Confidence** policy to:
   - `allow_with_warning` - Show warning but allow sales
   - `require_manager_override` - Require supervisor PIN (current)
   - `block_if_unverified` - Block sales until stock verified

### Fix 3: Ensure Items are Synced

```python
# Check if items are in offline sync queue
bench --site [site] console

from posawesome.posawesome.api.offline_sync import check_sync_status
status = check_sync_status()
print(f"Sync status: {status}")
```

## 📊 Verification Steps

### Check if Stock Cache is Ready

**Browser Console**:
```javascript
// Check IndexedDB for stock cache
indexedDB.open("posawesome").onsuccess = (event) => {
  const db = event.target.result;
  const transaction = db.transaction(["stock"], "readonly");
  const objectStore = transaction.objectStore("stock");
  const count = objectStore.count();
  count.onsuccess = () => {
    console.log("Stock entries in cache:", count.result);
  };
};
```

**Bench Console**:
```python
# Verify stock data
from frappe.db import get_value

# Check warehouse exists
warehouse = get_value("Warehouse", "Stores - LCL", "name")
print(f"Warehouse: {warehouse}")

# Check items have stock
from frappe.db import sql
stock_summary = sql("""
    SELECT
        COUNT(DISTINCT item_code) as items,
        SUM(actual_qty) as total_qty
    FROM `tabBin`
    WHERE warehouse LIKE '%LCL%'
""")

if stock_summary:
    print(f"Items with stock: {stock_summary[0][0]}")
    print(f"Total quantity: {stock_summary[0][1]}")
```

## 🚨 Common Scenarios

### Scenario 1: New Items Added

**Problem**: You created new items but they have no stock

**Solution**:
```python
bench --site [site] console
execfile('./apps/posawesome/create_lassod_items.py')
# Re-run stock creation
add_stock_to_item("NEW-ITEM-CODE", "Stores - LCL",
                 "Lassod Consulting Limited", qty=50)
```

### Scenario 2: Cache Corrupted

**Problem**: Warning persists even after sync

**Solution**:
```python
# Clear offline data from server side
bench --site [site] console

from frappe.cache import clear_cache
clear_cache()

# Also clear browser cache:
# 1. Open browser DevTools (F12)
# 2. Go to Application tab
# 3. Clear Storage > Clear site data
# 4. Reload POS
```

### Scenario 3: Operating Offline

**Problem**: You're intentionally offline and can't sync

**Solution**:
1. Use supervisor PIN to override (temporary)
2. Or change policy to `allow_with_warning`
3. Or reconnect to internet and sync

## 💡 Best Practices

1. **Always sync before going offline** - Ensure all data is current
2. **Regular stock updates** - Keep stock levels updated in system
3. **Clear cache periodically** - Prevents corruption buildup
4. **Monitor sync status** - Check Status menu regularly
5. **Train staff** - Ensure supervisors know their PINs

## 🔗 Related Files

- **frontend/src/offline/bootstrapSnapshot.ts** - Stock confidence logic
- **frontend/src/offline/stock.ts** - Stock cache management
- **frontend/src/offline/sync/adapters/stock.ts** - Stock sync adapter
- **posawesome/posawesome/api/item_processing/stock.py** - Stock API

## 📞 Quick Reference

**Warning Message**:
> "Stock confidence is low and a local supervisor override is required by policy.
> Collect a local supervisor PIN or privileged approval before selling uncertain stock.
> If the warning persists, open Status > Clear Cache."

**Immediate Actions**:
1. ✅ Connect to internet
2. ✅ Go to Status > Sync Now
3. ✅ Wait for sync to complete
4. ✅ Clear cache if needed (Status > Clear Cache)
5. ✅ Reload POS (Ctrl+R)

**If Warning Persists**:
1. Check stock exists in system
2. Add stock to items if needed
3. Clear browser cache
4. Use supervisor PIN as temporary workaround
5. Adjust offline policy in POS Profile

---

**Note**: The stock confidence system is designed to prevent overselling when stock data is uncertain. Using supervisor PIN acknowledges the risk and allows the sale to proceed.

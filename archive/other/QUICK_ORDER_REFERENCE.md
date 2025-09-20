# 🚀 Quick Reference: Order Execution

## Infrastructure Component
**Part of**: Chrome Management & Tradovate Interface  
**Full Docs**: `organized/docs/infrastructure/CHROME_TRADOVATE_ORDER_EXECUTION.md`

---

## 🔍 Daily Check (Every Morning)
```bash
python3 docs/investigations/dom-order-fix/final_order_verification.py
```
✅ If "SUCCESS!" → Ready to trade  
❌ If fails → Run emergency recovery

---

## 🏃 Quick Troubleshooting

### Orders Not Working?
1. **Check RIGHT Place**: `.module-dom .info-column .number` (positions)
2. **NOT**: `.module.orders` (order tables)

### Run This:
```bash
python3 src/utils/emergency_order_recovery.py
```

---

## 📊 Monitor During Trading
```bash
python3 src/utils/order_execution_monitor.py
```
Checks every 5 minutes that orders execute correctly

---

## 🚨 Emergency Fix
```bash
# Restart everything
./start_all.py
```

---

## 🔑 Key Insight
Orders were ALWAYS working. We were just checking the wrong place!
- ✅ DOM positions = Truth
- ❌ Order tables = May lag

---

**Full Documentation**: [Chrome-Tradovate Order Execution Infrastructure](organized/docs/infrastructure/CHROME_TRADOVATE_ORDER_EXECUTION.md)
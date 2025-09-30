# WMS • Inventory (FEFO) Dashboard Prototype

Single-screen dashboard to surface FEFO exposure and violations from SAP extracts.

## What it does
- Accepts **LT22 (RSVLFEFO Variant)** and **LX03 (RSVLFEFO Variant)** as upload refresh points.
- Computes tiles: Total FEFO Violations, LT22 Rows, Unique Materials, Min/Max SLED.
- Charts: **Violations by Storage Type (LT22)** and **Inventory by Expiry Bucket (LX03)**.
- Tables: Top Materials by Violations, Top Bins by Violations, Violations by User (from LT22), Expiry Buckets, Top Risk ≤60 days.
- Export: **pick_priority.csv** (Material → SLED → Batch) sorted FEFO.

## How to run (local)
1. Python 3.10+ recommended.
2. In a terminal:
```bash
cd wms_fefo_dashboard
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install flask pandas openpyxl matplotlib
python app.py
```
3. Open **http://localhost:5000**
4. Upload your **LT22.xlsx** and **LX03.xlsx** extracts.

## Notes
- No database required. Analysis is stored under `app_data/`.
- The look is intentionally **AS/400‑style** (green-on-black), per spec.
- If your LX03 workbook has multiple sheets, the app picks the **second** sheet (index 1) by default; otherwise it uses the only sheet.
- Robust to column header variations via fuzzy matching for key fields (Material, SLED/BBD, Total Stock, etc.).

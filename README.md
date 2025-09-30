# WMS • Inventory (FEFO) Dashboard (Single-Screen)

Single-screen dashboard to surface FEFO exposure and violations from SAP extracts (LT22 + LX03). Upload at the top of the dashboard—no extra menus.

## Features
- Tiles: Total FEFO Violations, LT22 Rows, Unique Materials, Min/Max SLED.
- Charts: Violations by Storage Type (LT22), Inventory by Expiry Bucket (LX03).
- Tables: Top Materials by Violations, Top Bins by Violations, Violations by User (LT22), Top Risk ≤60 days.
- Export: `pick_priority.csv` (Material → SLED/BBD → Batch) sorted FEFO.

## Run on Replit (one-click)
Open this URL after you push this repo to GitHub under your account:

```
https://replit.com/new/github/rcbt2000-byte/wms-fefo-dashboard
```

Replit will install dependencies and launch the app. Click **Open in new tab** when it starts.

## Local (optional)
```bash
pip install -r requirements.txt
python app.py
# open http://localhost:5000
```

## Notes
- `.replit` automates `pip install -r requirements.txt && python app.py`.
- `app_data/` stores generated charts/JSON and pick list.

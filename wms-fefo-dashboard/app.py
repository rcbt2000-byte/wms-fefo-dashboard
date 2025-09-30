#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WMS FEFO Dashboard Prototype (Single-screen)
- Upload LT22 & LX03 on the Dashboard
- Compute FEFO tiles
- Render AS/400-look dashboard
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_ROOT, 'app_data')
STATIC_DIR = os.path.join(APP_ROOT, 'static')

app = Flask(__name__)
app.secret_key = 'rsvl-fefo-demo'

# ---------- Helpers ----------

def find_col(cols, keys):
    for k in keys:
        for c in cols:
            try:
                if k.lower() in str(c).lower():
                    return c
            except Exception:
                pass
    return None


def safe_to_datetime(df, col):
    if col and col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')


def compute_analysis(lt22_path, lx03_path):
    # Load
    lt22 = pd.read_excel(lt22_path, sheet_name=0, engine='openpyxl')
    lt22.columns = [str(c).strip() for c in lt22.columns]

    # LX03: prefer sheet index 1 if multiple sheets exist
    try:
        xls = pd.ExcelFile(lx03_path, engine='openpyxl')
        sheet_to_use = 1 if len(xls.sheet_names) > 1 else 0
        lx03 = pd.read_excel(lx03_path, sheet_name=sheet_to_use, engine='openpyxl')
    except Exception:
        lx03 = pd.read_excel(lx03_path, sheet_name=0, engine='openpyxl')
    lx03.columns = [str(c).strip() for c in lx03.columns]

    # LT22 mapping
    mat_lt   = find_col(lt22.columns, ['Material'])
    qty_lt   = find_col(lt22.columns, ['Source target qty','Qty','Quantity'])
    sled_lt  = find_col(lt22.columns, ['SLED','BBD','expiration'])
    stype_lt = find_col(lt22.columns, ['Source Storage Type'])
    sbin_lt  = find_col(lt22.columns, ['Source Storage Bin'])
    batch_lt = find_col(lt22.columns, ['Batch'])
    user_lt  = find_col(lt22.columns, ['User'])
    expd_lt  = find_col(lt22.columns, ['EXP IN', 'EXP IN #'])
    old_lt   = find_col(lt22.columns, ['OLDEST IN SAP'])

    fefo_mask = lt22.apply(lambda row: row.astype(str).str.contains('FEFO VIOLATION', case=False, na=False).any(), axis=1)
    lt22['FEFO_VIOLATION'] = fefo_mask

    for col in [sled_lt, old_lt]:
        safe_to_datetime(lt22, col)

    if expd_lt and expd_lt in lt22.columns:
        lt22[expd_lt] = pd.to_numeric(lt22[expd_lt], errors='coerce')

    lt22_rows = len(lt22)
    lt22_violations = int(lt22['FEFO_VIOLATION'].sum())
    lt22_unique_materials = int(lt22[mat_lt].nunique()) if mat_lt else None
    min_sled = str(lt22[sled_lt].min().date()) if sled_lt and lt22[sled_lt].notna().any() else None
    max_sled = str(lt22[sled_lt].max().date()) if sled_lt and lt22[sled_lt].notna().any() else None

    viol = lt22[lt22['FEFO_VIOLATION']].copy()

    by_type = (viol.groupby(stype_lt).size().sort_values(ascending=False).reset_index(name='Violations')) if stype_lt else pd.DataFrame()
    by_mat  = (viol.groupby(mat_lt).size().sort_values(ascending=False).reset_index(name='Violations')) if mat_lt else pd.DataFrame()
    by_bin  = (viol.groupby(sbin_lt).size().sort_values(ascending=False).reset_index(name='Violations')) if sbin_lt else pd.DataFrame()
    by_user = (viol.groupby(user_lt).size().sort_values(ascending=False).reset_index(name='Violations')) if user_lt else pd.DataFrame()

    # LX03 mapping
    mat_lx  = find_col(lx03.columns, ['Material'])
    sled_lx = find_col(lx03.columns, ['SLED','BBD'])
    bin_lx  = find_col(lx03.columns, ['Storage Bin'])
    stp_lx  = find_col(lx03.columns, ['Storage Type'])
    qty_lx  = find_col(lx03.columns, ['Total Stock'])
    batch_lx= find_col(lx03.columns, ['Batch'])
    gr_lx   = find_col(lx03.columns, ['GR Date'])

    for col in [sled_lx, gr_lx]:
        safe_to_datetime(lx03, col)

    today = pd.to_datetime(datetime.today().date())
    if sled_lx and sled_lx in lx03.columns:
        lx03['DAYS_TO_EXP'] = (lx03[sled_lx] - today).dt.days
    else:
        lx03['DAYS_TO_EXP'] = np.nan

    if qty_lx and qty_lx in lx03.columns:
        lx03['qty'] = pd.to_numeric(lx03[qty_lx], errors='coerce')
    else:
        lx03['qty'] = np.nan

    def bucket2(d):
        if pd.isna(d): return 'Unknown'
        if d <= 0: return 'Expired/Past Due'
        if d <= 30: return '0-30'
        if d <= 60: return '31-60'
        if d <= 90: return '61-90'
        if d <= 150: return '91-150'
        return '150+'

    lx03['EXP_BUCKET'] = lx03['DAYS_TO_EXP'].apply(bucket2)
    exp_by_bucket_qty = (lx03.groupby('EXP_BUCKET')['qty'].sum()
                         .reindex(['Expired/Past Due','0-30','31-60','61-90','91-150','150+','Unknown'])
                         .fillna(0).reset_index(name='Total_Stock'))

    # Top risk ≤60 days
    at_risk_60 = lx03[(lx03['DAYS_TO_EXP']>=0) & (lx03['DAYS_TO_EXP']<=60)]
    if mat_lx and 'qty' in at_risk_60.columns:
        top_risk_60 = (at_risk_60.groupby(mat_lx)['qty']
                        .sum().sort_values(ascending=False).head(15)
                        .reset_index(name='Total_Stock_<=60d'))
    else:
        top_risk_60 = pd.DataFrame()

    # Pick Priority
    pp_cols = [c for c in [mat_lx, batch_lx, sled_lx, qty_lx, stp_lx, bin_lx] if c]
    pick_priority = lx03[pp_cols].copy() if pp_cols else pd.DataFrame()
    if not pick_priority.empty:
        pick_priority.rename(columns={mat_lx:'Material', batch_lx:'Batch', sled_lx:'SLED/BBD', qty_lx:'Total Stock', stp_lx:'Storage Type', bin_lx:'Storage Bin'}, inplace=True)
        pick_priority.sort_values(['Material','SLED/BBD','Batch'], inplace=True)

    # Charts
    plt.style.use('seaborn-v0_8')
    if by_type is not None and not by_type.empty:
        fig1, ax1 = plt.subplots(figsize=(7.2,3.6))
        ax1.bar(by_type.iloc[:,0].astype(str), by_type['Violations'], color='#32cd32')
        ax1.set_title('FEFO Violations by Storage Type (LT22)')
        ax1.set_xlabel('Storage Type')
        ax1.set_ylabel('Violations')
        plt.xticks(rotation=45, ha='right')
        fig1.tight_layout()
        fig1.savefig(os.path.join(STATIC_DIR, 'chart_viol_by_type.png'), dpi=150)
        plt.close(fig1)

    if exp_by_bucket_qty is not None and not exp_by_bucket_qty.empty:
        fig2, ax2 = plt.subplots(figsize=(7.2,3.6))
        ax2.bar(exp_by_bucket_qty['EXP_BUCKET'], exp_by_bucket_qty['Total_Stock'], color='#00ff90')
        ax2.set_title('Inventory by Expiry Bucket (LX03)')
        ax2.set_xlabel('Expiry bucket (days to SLED)')
        ax2.set_ylabel('Total Stock')
        fig2.tight_layout()
        fig2.savefig(os.path.join(STATIC_DIR, 'chart_exp_buckets.png'), dpi=150)
        plt.close(fig2)

    # Persist analysis
    results = {
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'cards': {
            'Total FEFO Violations': lt22_violations,
            'LT22 Rows': lt22_rows,
            'Unique Materials (LT22)': lt22_unique_materials,
            'Min/Max SLED (LT22)': f"{min_sled or '-'} → {max_sled or '-'}"
        },
        'tables': {}
    }

    if by_type is not None and not by_type.empty:
        results['tables']['Violations by Storage Type'] = by_type.to_dict(orient='records')
    if by_mat is not None and not by_mat.empty:
        results['tables']['Top Materials by Violations'] = by_mat.head(15).to_dict(orient='records')
    if by_bin is not None and not by_bin.empty:
        results['tables']['Top Bins by Violations'] = by_bin.head(15).to_dict(orient='records')
    if by_user is not None and not by_user.empty:
        results['tables']['Violations by User (LT22)'] = by_user.to_dict(orient='records')
    if exp_by_bucket_qty is not None and not exp_by_bucket_qty.empty:
        results['tables']['Inventory by Expiry Bucket (LX03)'] = exp_by_bucket_qty.to_dict(orient='records')
    if top_risk_60 is not None and not top_risk_60.empty:
        results['tables']['Top Risk Materials (≤60 days)'] = top_risk_60.to_dict(orient='records')

    analysis_path = os.path.join(DATA_DIR, 'analysis.json')
    with open(analysis_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(results, f, indent=2)

    if not pick_priority.empty:
        pick_priority.to_csv(os.path.join(DATA_DIR, 'pick_priority.csv'), index=False)

    return results

# ---------- Routes ----------

@app.route('/', methods=['GET'])
def index():
    # Always land on the dashboard (single-screen pattern)
    return redirect(url_for('dashboard'))

@app.route('/upload', methods=['POST'])
def upload():
    lt22_file = request.files.get('lt22')
    lx03_file = request.files.get('lx03')
    if not lt22_file or not lx03_file:
        flash('Please upload both LT22 and LX03 files.')
        return redirect(url_for('dashboard'))

    os.makedirs(DATA_DIR, exist_ok=True)
    lt22_path = os.path.join(DATA_DIR, 'LT22.xlsx')
    lx03_path = os.path.join(DATA_DIR, 'LX03.xlsx')
    lt22_file.save(lt22_path)
    lx03_file.save(lx03_path)

    try:
        compute_analysis(lt22_path, lx03_path)
        flash('Files processed successfully.')
    except Exception as e:
        flash(f'Processing error: {e}')
    return redirect(url_for('dashboard'))

@app.route('/dashboard', methods=['GET'])
def dashboard():
    import json
    analysis_file = os.path.join(DATA_DIR, 'analysis.json')
    if os.path.exists(analysis_file):
        with open(analysis_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
    else:
        results = None
    charts = []
    for fn in ['chart_viol_by_type.png', 'chart_exp_buckets.png']:
        p = os.path.join(STATIC_DIR, fn)
        if os.path.exists(p):
            charts.append(fn)
    pick_csv = os.path.exists(os.path.join(DATA_DIR, 'pick_priority.csv'))
    return render_template('dashboard.html', results=results, charts=charts, pick_csv=pick_csv)

@app.route('/download/<path:fname>')
def download(fname):
    return send_from_directory(DATA_DIR, fname, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=True)

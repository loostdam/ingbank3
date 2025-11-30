from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

DATA_FILE = 'data/transactions.json'
LABELS_FILE = 'data/labels.json'
UPLOAD_FOLDER = 'uploads'

os.makedirs('data', exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_transactions():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_transactions(transactions):
    with open(DATA_FILE, 'w') as f:
        json.dump(transactions, f, indent=2)

def load_labels():
    if os.path.exists(LABELS_FILE):
        with open(LABELS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_labels(labels):
    with open(LABELS_FILE, 'w') as f:
        json.dump(labels, f, indent=2)

def parse_ing_excel(file_path):
    df = pd.read_excel(file_path)
    transactions = []
    
    for _, row in df.iterrows():
        date_str = str(row['Date'])
        if len(date_str) == 8:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            formatted_date = f"{year}-{month:02d}-{day:02d}"
        else:
            formatted_date = date_str
        
        amount_str = str(row['Amount (EUR)']).replace(',', '.')
        try:
            amount = float(amount_str)
        except ValueError:
            amount = 0.0
        
        if row['Debit/credit'] == 'Debit':
            amount = -abs(amount)
        else:
            amount = abs(amount)
        
        transaction = {
            'id': len(transactions) + 1,
            'date': formatted_date,
            'description': str(row['Name / Description']),
            'counterparty': str(row['Counterparty']) if pd.notna(row['Counterparty']) else '',
            'amount': amount,
            'type': row['Debit/credit'],
            'transaction_type': str(row['Transaction type']) if pd.notna(row['Transaction type']) else '',
            'notifications': str(row['Notifications']) if pd.notna(row['Notifications']) else '',
            'label': ''
        }
        transactions.append(transaction)
    
    return transactions

@app.route('/')
def index():
    transactions = load_transactions()
    labels = load_labels()
    return render_template('index.html', transactions=transactions, labels=labels)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if file and file.filename and file.filename.endswith(('.xlsx', '.xls')):
        filepath = os.path.join(UPLOAD_FOLDER, str(file.filename))
        file.save(filepath)
        
        try:
            new_transactions = parse_ing_excel(filepath)
            existing = load_transactions()
            
            existing_keys = set()
            for t in existing:
                key = f"{t['date']}_{t['description']}_{t['amount']}"
                existing_keys.add(key)
            
            added = 0
            for t in new_transactions:
                key = f"{t['date']}_{t['description']}_{t['amount']}"
                if key not in existing_keys:
                    t['id'] = len(existing) + added + 1
                    existing.append(t)
                    added += 1
            
            save_transactions(existing)
            flash(f'Successfully imported {added} new transactions!', 'success')
        except Exception as e:
            flash(f'Error importing file: {str(e)}', 'error')
    else:
        flash('Please upload an Excel file (.xlsx or .xls)', 'error')
    
    return redirect(url_for('index'))

@app.route('/add_label', methods=['POST'])
def add_label():
    label_name = request.form.get('label_name', '').strip()
    label_color = request.form.get('label_color', '#3b82f6')
    
    if label_name:
        labels = load_labels()
        if not any(l['name'] == label_name for l in labels):
            labels.append({'name': label_name, 'color': label_color})
            save_labels(labels)
            flash(f'Label "{label_name}" added!', 'success')
        else:
            flash('Label already exists', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete_label/<label_name>', methods=['POST'])
def delete_label(label_name):
    labels = load_labels()
    labels = [l for l in labels if l['name'] != label_name]
    save_labels(labels)
    
    transactions = load_transactions()
    for t in transactions:
        if t.get('label') == label_name:
            t['label'] = ''
    save_transactions(transactions)
    
    flash(f'Label "{label_name}" deleted!', 'success')
    return redirect(url_for('index'))

@app.route('/assign_label', methods=['POST'])
def assign_label():
    transaction_id = request.form.get('transaction_id')
    label = request.form.get('label', '')
    
    transactions = load_transactions()
    for t in transactions:
        if str(t['id']) == str(transaction_id):
            t['label'] = label
            break
    
    save_transactions(transactions)
    return jsonify({'success': True})

@app.route('/bulk_assign', methods=['POST'])
def bulk_assign():
    data = request.get_json()
    transaction_ids = data.get('transaction_ids', [])
    label = data.get('label', '')
    
    transactions = load_transactions()
    for t in transactions:
        if str(t['id']) in [str(tid) for tid in transaction_ids]:
            t['label'] = label
    
    save_transactions(transactions)
    return jsonify({'success': True})

@app.route('/overview')
def overview():
    transactions = load_transactions()
    labels = load_labels()
    
    years = set()
    for t in transactions:
        try:
            t_year = int(t['date'][:4])
            years.add(t_year)
        except:
            pass
    years = sorted(years, reverse=True)
    if not years:
        years = [datetime.now().year]
    
    default_year = years[0] if years else datetime.now().year
    year = request.args.get('year', default_year, type=int)
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    overview_data = {}
    label_colors = {l['name']: l['color'] for l in labels}
    label_colors['Unlabeled'] = '#6b7280'
    
    all_labels = [l['name'] for l in labels] + ['Unlabeled']
    
    for label in all_labels:
        overview_data[label] = {
            'color': label_colors.get(label, '#6b7280'),
            'months': {i+1: 0 for i in range(12)},
            'total': 0
        }
    
    for t in transactions:
        try:
            t_year = int(t['date'][:4])
            t_month = int(t['date'][5:7])
            
            if t_year == year:
                label = t.get('label', '') or 'Unlabeled'
                if label in overview_data:
                    overview_data[label]['months'][t_month] += t['amount']
                    overview_data[label]['total'] += t['amount']
        except:
            pass
    
    monthly_totals = {i+1: 0 for i in range(12)}
    grand_total = 0
    
    for label, data in overview_data.items():
        for month, amount in data['months'].items():
            monthly_totals[month] += amount
        grand_total += data['total']
    
    return render_template('overview.html', 
                         overview_data=overview_data, 
                         months=months, 
                         year=year, 
                         years=years,
                         monthly_totals=monthly_totals,
                         grand_total=grand_total)

@app.route('/clear_data', methods=['POST'])
def clear_data():
    save_transactions([])
    flash('All transactions cleared!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

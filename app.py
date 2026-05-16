from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DATABASE = 'smart_building_maintenance.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    conn = get_db_connection()
    building_count = conn.execute('SELECT COUNT(*) FROM Buildings').fetchone()[0]
    asset_count = conn.execute('SELECT COUNT(*) FROM Assets').fetchone()[0]
    pending_count = conn.execute("SELECT COUNT(*) FROM Maintenance_Requests WHERE repair_status='Pending'").fetchone()[0]
    completed_count = conn.execute("SELECT COUNT(*) FROM Maintenance_Requests WHERE repair_status='Completed'").fetchone()[0]
    recent_requests = conn.execute('''
        SELECT mr.request_id, a.asset_name, mr.issue_description, mr.repair_status
        FROM Maintenance_Requests mr
        JOIN Assets a ON mr.asset_id = a.asset_id
        ORDER BY mr.request_date DESC
        LIMIT 5
    ''').fetchall()
    conn.close()
    return render_template('dashboard.html',
                           building_count=building_count,
                           asset_count=asset_count,
                           pending_count=pending_count,
                           completed_count=completed_count,
                           recent_requests=recent_requests)

@app.route('/assets')
def assets():
    conn = get_db_connection()
    assets = conn.execute('''
        SELECT Assets.*, Rooms.room_name
        FROM Assets
        JOIN Rooms ON Assets.room_id = Rooms.room_id
    ''').fetchall()
    conn.close()
    return render_template('assets.html', assets=assets)

@app.route('/add_asset', methods=('GET', 'POST'))
def add_asset():
    conn = get_db_connection()
    rooms = conn.execute('SELECT * FROM Rooms').fetchall()
    if request.method == 'POST':
        conn.execute('''
            INSERT INTO Assets (room_id, asset_name, category, purchase_date, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            request.form['room_id'],
            request.form['asset_name'],
            request.form['category'],
            request.form['purchase_date'],
            request.form['status']
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('assets'))
    conn.close()
    return render_template('add_asset.html', rooms=rooms, asset=None)

@app.route('/edit_asset/<int:id>', methods=('GET', 'POST'))
def edit_asset(id):
    conn = get_db_connection()
    asset = conn.execute('SELECT * FROM Assets WHERE asset_id=?', (id,)).fetchone()
    rooms = conn.execute('SELECT * FROM Rooms').fetchall()
    if request.method == 'POST':
        conn.execute('''
            UPDATE Assets
            SET room_id=?, asset_name=?, category=?, purchase_date=?, status=?
            WHERE asset_id=?
        ''', (
            request.form['room_id'],
            request.form['asset_name'],
            request.form['category'],
            request.form['purchase_date'],
            request.form['status'],
            id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('assets'))
    conn.close()
    return render_template('edit_asset.html', asset=asset, rooms=rooms)

@app.route('/delete_asset/<int:id>')
def delete_asset(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Assets WHERE asset_id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('assets'))

@app.route('/requests')
def requests_page():
    conn = get_db_connection()
    requests = conn.execute('''
        SELECT mr.*, a.asset_name, t.technician_name
        FROM Maintenance_Requests mr
        JOIN Assets a ON mr.asset_id = a.asset_id
        LEFT JOIN Technicians t ON mr.technician_id = t.technician_id
    ''').fetchall()
    conn.close()
    return render_template('requests.html', requests=requests)

@app.route('/add_request', methods=('GET', 'POST'))
def add_request():
    conn = get_db_connection()
    assets = conn.execute('SELECT * FROM Assets').fetchall()
    technicians = conn.execute('SELECT * FROM Technicians').fetchall()
    if request.method == 'POST':
        conn.execute('''
            INSERT INTO Maintenance_Requests (asset_id, technician_id, issue_description, request_date, repair_status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            request.form['asset_id'],
            request.form['technician_id'],
            request.form['issue_description'],
            request.form['request_date'],
            request.form['repair_status']
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('requests_page'))
    conn.close()
    return render_template('add_request.html', assets=assets, technicians=technicians)

if __name__ == '__main__':
    app.run(debug=True)
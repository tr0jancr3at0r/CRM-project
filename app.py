from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'database.db'))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            login TEXT UNIQUE,
            password TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT,
            startDate TEXT,
            endDate TEXT,
            budget REAL,
            description TEXT,
            date TEXT,
            time TEXT,
            status TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT,
            debt REAL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            clientId INTEGER,
            type TEXT,
            endDate TEXT,
            totalSum REAL,
            status TEXT,
            description TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS projectItems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projectId INTEGER,
            name TEXT,
            qty REAL,
            price REAL,
            sum REAL,
            taxRate REAL,
            tax REAL,
            cost REAL,
            total REAL,
            profit REAL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS projectTypes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projectId INTEGER,
            name TEXT,
            type TEXT,
            date TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clientId INTEGER,
            text TEXT,
            rating INTEGER,
            date TEXT
        )''')

        admin = conn.execute("SELECT * FROM admins WHERE login='admin'").fetchone()
        if not admin:
            conn.execute("INSERT INTO admins (name, login, password) VALUES ('Администратор', 'admin', 'admin')")

        default_types = ['Ремонт', 'Строительство', 'Дизайн', 'Интеграция']
        for t in default_types:
            conn.execute("INSERT OR IGNORE INTO projectTypes (name) VALUES (?)", (t,))

        count = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        if count == 0:
            conn.execute('''INSERT INTO requests 
                (name, phone, email, startDate, endDate, budget, description, date, time, status)
                VALUES (?,?,?,?,?,?,?,?,?,?)''',
                ('Алексей Смирнов', '+7 912 333-44-55', 'alex@mail.ru',
                 '2025-02-01', '2025-03-15', 150000,
                 'Разработать корпоративный сайт с каталогом товаров',
                 '2025-01-20', '14:30', 'новая'))

        client_count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        if client_count == 0:
            conn.execute("INSERT INTO clients (name, phone, email, debt) VALUES (?,?,?,?)",
                         ('ООО "ТехноПарк"', '+7 495 111-22-33', 'info@technopark.ru', 0))

        project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        if project_count == 0:
            conn.execute('''INSERT INTO projects 
                (name, clientId, type, endDate, totalSum, status, description)
                VALUES (?,?,?,?,?,?,?)''',
                ('Обновление серверов', 1, 'Интеграция', '2025-12-31', 250000, 'В работе', 'Замена оборудования'))

        conn.commit()

init_db()

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    login = data.get('login')
    password = data.get('password')
    with get_db() as conn:
        row = conn.execute("SELECT * FROM admins WHERE login=? AND password=?", (login, password)).fetchone()
        if row:
            return jsonify(dict(row))
        else:
            return jsonify({'error': 'Неверные данные'}), 401

@app.route('/api/admin/register', methods=['POST'])
def admin_register():
    data = request.json
    name = data.get('name')
    login = data.get('login')
    password = data.get('password')
    if not name or not login or not password:
        return jsonify({'error': 'Заполните все поля'}), 400
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM admins WHERE login=?", (login,)).fetchone()
        if existing:
            return jsonify({'error': 'Такой логин уже существует'}), 400
        conn.execute("INSERT INTO admins (name, login, password) VALUES (?,?,?)", (name, login, password))
        conn.commit()
        return jsonify({'message': 'OK'}), 201

@app.route('/api/requests', methods=['GET'])
def get_requests():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM requests ORDER BY id DESC").fetchall()
        return jsonify([dict(row) for row in rows])

@app.route('/api/requests', methods=['POST'])
def add_request():
    data = request.json
    with get_db() as conn:
        cur = conn.execute('''INSERT INTO requests 
            (name, phone, email, startDate, endDate, budget, description, date, time, status)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (data['name'], data['phone'], data['email'], data.get('startDate',''), data.get('endDate',''),
             data.get('budget', 0), data['description'],
             datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%H:%M'), 'новая'))
        conn.commit()
        return jsonify({'id': cur.lastrowid}), 201

@app.route('/api/requests/<int:req_id>', methods=['DELETE'])
def delete_request(req_id):
    with get_db() as conn:
        conn.execute("DELETE FROM requests WHERE id=?", (req_id,))
        conn.commit()
        return jsonify({'message': 'OK'})

@app.route('/api/requests/<int:req_id>', methods=['PUT'])
def update_request(req_id):
    data = request.json
    with get_db() as conn:
        conn.execute("UPDATE requests SET status=? WHERE id=?", (data.get('status', 'новая'), req_id))
        conn.commit()
        return jsonify({'message': 'OK'})

@app.route('/api/clients', methods=['GET'])
def get_clients():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM clients ORDER BY id DESC").fetchall()
        return jsonify([dict(row) for row in rows])

@app.route('/api/clients', methods=['POST'])
def add_client():
    data = request.json
    with get_db() as conn:
        cur = conn.execute("INSERT INTO clients (name, phone, email, debt) VALUES (?,?,?,?)",
                           (data['name'], data.get('phone',''), data.get('email',''), data.get('debt', 0)))
        conn.commit()
        return jsonify({'id': cur.lastrowid}), 201

@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    data = request.json
    with get_db() as conn:
        conn.execute("UPDATE clients SET name=?, phone=?, email=?, debt=? WHERE id=?",
                     (data['name'], data.get('phone',''), data.get('email',''), data.get('debt', 0), client_id))
        conn.commit()
        return jsonify({'message': 'OK'})

@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    with get_db() as conn:
        conn.execute("DELETE FROM clients WHERE id=?", (client_id,))
        conn.commit()
        return jsonify({'message': 'OK'})

@app.route('/api/projects', methods=['GET'])
def get_projects():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
        return jsonify([dict(row) for row in rows])

@app.route('/api/projects', methods=['POST'])
def add_project():
    data = request.json
    with get_db() as conn:
        cur = conn.execute('''INSERT INTO projects 
            (name, clientId, type, endDate, totalSum, status, description)
            VALUES (?,?,?,?,?,?,?)''',
            (data['name'], data['clientId'], data.get('type',''), data.get('endDate',''),
             data.get('totalSum',0), data.get('status','Новый'), data.get('description','')))
        conn.commit()
        return jsonify({'id': cur.lastrowid}), 201

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    data = request.json
    with get_db() as conn:
        conn.execute('''UPDATE projects SET 
            name=?, clientId=?, type=?, endDate=?, totalSum=?, status=?, description=?
            WHERE id=?''',
            (data['name'], data['clientId'], data.get('type',''), data.get('endDate',''),
             data.get('totalSum',0), data.get('status','Новый'), data.get('description',''), project_id))
        conn.commit()
        return jsonify({'message': 'OK'})

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    with get_db() as conn:
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        conn.execute("DELETE FROM projectItems WHERE projectId=?", (project_id,))
        conn.commit()
        return jsonify({'message': 'OK'})

@app.route('/api/project-items', methods=['GET'])
def get_project_items():
    project_id = request.args.get('projectId')
    if not project_id:
        return jsonify([])
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM projectItems WHERE projectId=? ORDER BY id", (project_id,)).fetchall()
        return jsonify([dict(row) for row in rows])

@app.route('/api/project-items', methods=['POST'])
def add_project_item():
    data = request.json

    sum_val = data['qty'] * data['price']
    tax = sum_val * (data['taxRate'] / 100)
    total = data['qty'] * data['cost'] + tax
    profit = sum_val - total
    with get_db() as conn:
        cur = conn.execute('''INSERT INTO projectItems 
            (projectId, name, qty, price, sum, taxRate, tax, cost, total, profit)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (data['projectId'], data['name'], data['qty'], data['price'],
             sum_val, data['taxRate'], tax, data['cost'], total, profit))
        conn.commit()
        return jsonify({'id': cur.lastrowid}), 201

@app.route('/api/project-items/<int:item_id>', methods=['PUT'])
def update_project_item(item_id):
    data = request.json

    sum_val = data['qty'] * data['price']
    tax = sum_val * (data['taxRate'] / 100)
    total = data['qty'] * data['cost'] + tax
    profit = sum_val - total
    with get_db() as conn:
        conn.execute('''UPDATE projectItems SET
            name=?, qty=?, price=?, sum=?, taxRate=?, tax=?, cost=?, total=?, profit=?
            WHERE id=?''',
            (data['name'], data['qty'], data['price'], sum_val, data['taxRate'], tax,
             data['cost'], total, profit, item_id))
        conn.commit()
        return jsonify({'message': 'OK'})

@app.route('/api/project-items/<int:item_id>', methods=['DELETE'])
def delete_project_item(item_id):
    with get_db() as conn:
        conn.execute("DELETE FROM projectItems WHERE id=?", (item_id,))
        conn.commit()
        return jsonify({'message': 'OK'})

@app.route('/api/project-types', methods=['GET'])
def get_project_types():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM projectTypes ORDER BY name").fetchall()
        return jsonify([dict(row) for row in rows])

@app.route('/api/project-types', methods=['POST'])
def add_project_type():
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Введите название'}), 400
    with get_db() as conn:
        try:
            cur = conn.execute("INSERT INTO projectTypes (name) VALUES (?)", (name,))
            conn.commit()
            return jsonify({'id': cur.lastrowid}), 201
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Такой тип уже существует'}), 400

@app.route('/api/project-types/<int:type_id>', methods=['DELETE'])
def delete_project_type(type_id):
    with get_db() as conn:
        conn.execute("DELETE FROM projectTypes WHERE id=?", (type_id,))
        conn.commit()
        return jsonify({'message': 'OK'})

def project_total(conn, project_id):
    row = conn.execute("SELECT COALESCE(SUM(profit),0) AS total FROM projectItems WHERE projectId=?",
                       (project_id,)).fetchone()
    return row['total'] if row else 0

@app.route('/api/orders', methods=['GET'])
def get_orders():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        result = []
        for row in rows:
            o = dict(row)
            o['sum'] = project_total(conn, o['projectId'])
            result.append(o)
        return jsonify(result)

@app.route('/api/orders', methods=['POST'])
def add_order():
    data = request.json
    with get_db() as conn:
        cur = conn.execute("INSERT INTO orders (projectId, name, type, date) VALUES (?,?,?,?)",
                           (data['projectId'], data.get('name',''), data.get('type',''),
                            datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        return jsonify({'id': cur.lastrowid}), 201

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.json
    with get_db() as conn:
        conn.execute("UPDATE orders SET projectId=?, name=?, type=? WHERE id=?",
                     (data['projectId'], data.get('name',''), data.get('type',''), order_id))
        conn.commit()
        return jsonify({'message': 'OK'})

@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    with get_db() as conn:
        conn.execute("DELETE FROM orders WHERE id=?", (order_id,))
        conn.commit()
        return jsonify({'message': 'OK'})

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    client_id = request.args.get('clientId')
    with get_db() as conn:
        if client_id:
            rows = conn.execute("SELECT * FROM reviews WHERE clientId=? ORDER BY id DESC", (client_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM reviews ORDER BY id DESC").fetchall()
        return jsonify([dict(row) for row in rows])

@app.route('/api/reviews', methods=['POST'])
def add_review():
    data = request.json
    with get_db() as conn:
        cur = conn.execute("INSERT INTO reviews (clientId, text, rating, date) VALUES (?,?,?,?)",
                           (data['clientId'], data.get('text',''), data.get('rating', 5),
                            datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        return jsonify({'id': cur.lastrowid}), 201

@app.route('/api/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    with get_db() as conn:
        conn.execute("DELETE FROM reviews WHERE id=?", (review_id,))
        conn.commit()
        return jsonify({'message': 'OK'})

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:path>')
def catch_all(path):
    if os.path.exists(os.path.join(BASE_DIR, path)):
        return send_from_directory(BASE_DIR, path)
    return send_from_directory(BASE_DIR, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_PATH = 'database.db'

def init_db():
    """Инициализация базы данных с тестовыми данными"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Создание таблицы
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE app_secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            secret TEXT NOT NULL
        )
    ''')
    
    # Добавление тестовых данных
    test_users = [
        ('alice',   'alice123',   'user'),
        ('bob',     'qwerty123',  'user'),
        ('admin',   'admin123',   'admin'),
        ('charlie', 'welcome123', 'moderator'),
        ('david',   'password1',  'user'),
    ]
    
    for username, password, role in test_users:
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                      (username, password, role))
    
    # Данные app_secrets
    test_secrets = [
        ('internal_api_key', 'AKIA_TEST_9F3K2L1M'),
        ('jwt_signing_key',  'dev_jwt_key_change_me'),
        ('smtp_password',    'smtp-pass-2025'),
    ]
    for name, secret in test_secrets:
        cursor.execute(
            'INSERT INTO app_secrets (name, secret) VALUES (?, ?)',
            (name, secret)
        )
    conn.commit()
    conn.close()
    print('db is inited')

def get_connection():
    """Получить соединение с БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Главная страница - поиск пользователей (УЯЗВИМО к SQLi в GET)"""
    query = request.args.get('q', '')
    users = []
    error = None
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # ⚠️ УЯЗВИМОСТЬ: Прямая конкатенация пользовательского ввода
        sql = f"SELECT id, username, password, role FROM users WHERE username LIKE '%{query}%' ORDER BY id"
        
        cursor.execute(sql)
        users = cursor.fetchall()
        conn.close()
    except Exception as e:
        error = f"SQL Error: {str(e)}"
    
    return render_template('index.html', 
                         users=users, 
                         error=error,
                         request=request)

@app.route('/create', methods=['POST'])
def create():
    """Создание пользователя (УЯЗВИМО к SQLi в POST)"""
    username = request.form.get('username', '')
    role = request.form.get('role', '')
    password = request.form.get('password', '')
    message = None
    message_type = 'info'
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # ⚠️ УЯЗВИМОСТЬ: Прямая конкатенация пользовательского ввода в INSERT
        sql = f"INSERT INTO users (username, password, role) VALUES ('{username}', {password}, '{role}')"
        
        cursor.execute(sql)
        conn.commit()
        conn.close()
        
        message = f"✅ Пользователь '{username}' успешно создан с ролью '{role}'"
        message_type = 'success'
    except Exception as e:
        message = f"❌ Ошибка: {str(e)}"
        message_type = 'error'
    
    return redirect(url_for('index', _anchor='create', message=message, message_type=message_type))

@app.errorhandler(404)
def not_found(e):
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Инициализация БД при первом запуске
    if not os.path.exists(DB_PATH):
        init_db()
    
    app.run(debug=True, host='127.0.0.1', port=5000)

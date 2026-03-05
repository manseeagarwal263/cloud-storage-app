from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mysecretkey123"

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                password TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                filename TEXT,
                file_url TEXT,
                upload_date TEXT,
                file_size INTEGER)''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data['username']
        email = data['email']
        password = data['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        if c.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Email already registered!'})
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                  (username, email, password))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data['email']
        password = data['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid email or password!'})
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM files WHERE user_id=?", (session['user_id'],))
    files = c.fetchall()
    conn.close()
    return render_template('dashboard.html', files=files, username=session['username'])

@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    upload_folder = 'static/uploads'
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, file.filename)
    file.save(filepath)
    file_size = os.path.getsize(filepath) // 1024
    file_url = '/' + filepath.replace('\\', '/')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO files (user_id, filename, file_url, upload_date, file_size) VALUES (?, ?, ?, ?, ?)",
              (session['user_id'], file.filename, file_url, datetime.now().strftime('%Y-%m-%d %H:%M'), file_size))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/delete/<int:file_id>')
def delete(file_id):
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM files WHERE id=? AND user_id=?", (file_id, session['user_id']))
    file = c.fetchone()
    if file:
        filepath = file[3].lstrip('/')
        if os.path.exists(filepath):
            os.remove(filepath)
        c.execute("DELETE FROM files WHERE id=?", (file_id,))
        conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
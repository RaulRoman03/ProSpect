from flask import Flask, render_template, request, redirect, session, url_for, flash
from pymongo import MongoClient, errors
import os
import sys

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey")

MONGO_URI = os.environ.get("MONGO_URI")
users = None

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    client.server_info()
    db = client.get_default_database()
    users = db.users
except errors.ServerSelectionTimeoutError as e:
    print("ERROR: No se pudo conectar a MongoDB:", e, file=sys.stderr)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if not users:
        flash("Base de datos no disponible", "error")
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if users.find_one({'username': username}):
            flash("El usuario ya existe", "error")
            return redirect(url_for('register'))

        users.insert_one({'username': username, 'password': password, 'role': 'player'})
        flash("Registro exitoso", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not users:
        flash("Base de datos no disponible", "error")
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = users.find_one({'username': username, 'password': password})
        if user:
            session['username'] = username
            session['role'] = user.get('role', 'player')
            return redirect(url_for(user['role']))
        else:
            flash("Credenciales incorrectas", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/player')
def player():
    if session.get('role') != 'player':
        return redirect(url_for('login'))
    return render_template('player.html')

@app.route('/coach')
def coach():
    if session.get('role') != 'coach':
        return redirect(url_for('login'))
    return render_template('coach.html')

@app.route('/recruiter')
def recruiter():
    if session.get('role') != 'recruiter':
        return redirect(url_for('login'))
    return render_template('recruiter.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/reset', methods=['GET', 'POST'])
def password_reset():
    if request.method == 'POST':
        flash("Si el usuario existe, se enviará un correo con instrucciones.", "info")
        return redirect(url_for('login'))
    return render_template('password_reset.html')

if __name__ == '__main__':
    app.run(debug=True)
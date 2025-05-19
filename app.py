from flask import Flask, render_template, request, redirect, session, url_for, flash
from pymongo import MongoClient, errors
import os
import sys

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey")

MONGO_URI = os.environ.get("MONGO_URI")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    client.server_info()
    db = client.get_default_database()
    users = db.users
except errors.ServerSelectionTimeoutError as e:
    print("ERROR: No se pudo conectar a MongoDB:", e, file=sys.stderr)
    users = None

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
        role     = request.form.get('role')
        if not username or not password or not role:
            flash("Completa todos los campos", "error")
            return render_template('register.html')
        if users.find_one({'username': username}):
            flash("El usuario ya existe", "error")
            return render_template('register.html')
        users.insert_one({'username': username, 'password': password, 'role': role})
        flash("Registro exitoso, ahora inicia sesión", "success")
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
        role     = request.form.get('role')
        if not username or not password or not role:
            flash("Completa todos los campos", "error")
            return render_template('login.html')
        user = users.find_one({'username': username})
        if user and user['password'] == password and user['role'] == role:
            session['user_id']  = str(user['_id'])
            session['username'] = user['username']
            session['role']     = user['role']
            return redirect(url_for('dashboard'))

        flash('Credenciales incorrectas', 'error')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    role = session['role']
    username = session['username']

    if role == 'player':
        return render_template('player.html', username=username)
    if role == 'coach':
        return render_template('coach.html', username=username)
    if role == 'recruiter':
        return render_template('recruiter.html', username=username)

    # rol desconocido: cerramos sesión
    return redirect(url_for('logout'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Ruta para recuperación de contraseña
@app.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    # placeholder: implementa tu lógica
    if request.method == 'POST':
        flash("Funcionalidad de recuperación aún no implementada", "info")
    return render_template('password_reset.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    # Modo debug para ver traceback en el navegador
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
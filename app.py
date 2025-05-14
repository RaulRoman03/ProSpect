from flask import Flask, render_template, request, redirect, session, url_for, flash
from pymongo import MongoClient
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey")

MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_default_database()
users = db.users

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        user = {
            'username': request.form['username'],
            'password': request.form['password'],
            'role': role
        }
        if users.find_one({'username': user['username']}):
            return render_template('register.html', error='Usuario ya existe')
        users.insert_one(user)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = users.find_one({'username': request.form['username']})
        if user and user['password'] == request.form['password']:
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        
        flash('Credenciales incorrectas. Por favor intenta nuevamente.', 'error')
        return render_template('login.html', form_data=request.form)
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    role = session.get('role')
    username = session.get('username')
    
    if role == 'player':
        return render_template('player.html', username=username)
    elif role == 'coach':
        return render_template('coach.html', username=username)
    elif role == 'recruiter':
        return render_template('recruiter.html', username=username)
    else:
        return redirect(url_for('logout'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Ruta provisoria para el enlace "¿Olvidaste tu contraseña?"
@app.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    # Implementa la lógica real aquí
    return render_template('password_reset.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
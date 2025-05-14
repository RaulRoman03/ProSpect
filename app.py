from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
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
            return 'Usuario ya existe'
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
        return 'Credenciales incorrectas'
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    role = session.get('role')
    if role == 'player':
        return render_template('player.html', username=session['username'])
    elif role == 'coach':
        return render_template('coach.html', username=session['username'])
    elif role == 'recruiter':
        return render_template('recruiter.html', username=session['username'])
    else:
        return 'Rol no reconocido'

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
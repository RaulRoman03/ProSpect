from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson import ObjectId
import os

app = Flask(__name__)
app.secret_key = 'secretkey'

# Conexión a MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["proyectofinal"]
users = db["users"]
videos = db["videos"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['role'] = user['role']
            if user['role'] == 'player':
                return redirect(url_for('player'))
            elif user['role'] == 'coach':
                return redirect(url_for('coach'))
            elif user['role'] == 'recruiter':
                return redirect(url_for('recruiter'))
        else:
            flash('Credenciales inválidas. Inténtalo de nuevo.', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        nombre = request.form['nombre']
        edad = request.form['edad']
        posicion = request.form['posicion']
        password = request.form['password']
        role = request.form['role']

        if users.find_one({'username': username}):
            flash('El nombre de usuario ya existe.', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        users.insert_one({
            'username': username,
            'nombre': nombre,
            'edad': edad,
            'posicion': posicion,
            'password': hashed_password,
            'role': role
        })
        flash('Registro exitoso. Inicia sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/player')
def player():
    if 'username' not in session or session.get('role') != 'player':
        return redirect(url_for('login'))

    username = session['username']
    user = users.find_one({'username': username})
    user_videos = list(videos.find({'user': username}).sort('timestamp', -1)) if videos else []

    return render_template('player.html', user=user, videos=user_videos)

@app.route('/recruiter')
def recruiter():
    if 'username' not in session or session.get('role') != 'recruiter':
        return redirect(url_for('login'))

    players = list(users.find({'role': 'player'}))
    return render_template('recruiter.html', players=players)

@app.route('/coach')
def coach():
    if 'username' not in session or session.get('role') != 'coach':
        return redirect(url_for('login'))

    players = list(users.find({'role': 'player'}))
    return render_template('coach.html', players=players)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Nueva ruta para el perfil del jugador
@app.route('/player/<username>')
def player_profile(username):
    if session.get('role') != 'recruiter':
        return redirect(url_for('login'))

    player = users.find_one({'username': username, 'role': 'player'})
    player_videos = list(videos.find({'user': username}).sort('timestamp', -1)) if videos else []

    if not player:
        flash("Jugador no encontrado", "error")
        return redirect(url_for('recruiter'))

    return render_template('player_profile.html', player=player, videos=player_videos)

if __name__ == '__main__':
    app.run(debug=True)
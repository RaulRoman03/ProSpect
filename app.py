from flask import Flask, render_template, request, redirect, session, url_for, flash
from pymongo import MongoClient, errors
from datetime import datetime
import os
import sys
import cloudinary.uploader

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey")

MONGO_URI = os.environ.get("MONGO_URI")
cloud_name = os.environ.get("cloud_name")
api_key = os.environ.get("api_key")
api_secret = os.environ.get("api_secret")

users = None
videos = None

cloudinary.config(
    cloud_name=cloud_name,
    api_key=api_key,
    api_secret=api_secret,
    secure=True
)

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    client.server_info()
    db = client.get_default_database()
    users = db.users
    videos = db.media
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
        role = request.form.get('role')
        age_range = request.form.get('age_range')
        position = request.form.get('position')

        form_data = request.form.to_dict()

        if not username or not password or not role:
            flash("Todos los campos son obligatorios", "error")
            return render_template('register.html', form_data=form_data)

        if role not in ['player', 'coach', 'recruiter']:
            flash("Rol inválido", "error")
            return render_template('register.html', form_data=form_data)

        if users.find_one({'username': username}):
            flash("El usuario ya existe", "error")
            return render_template('register.html', form_data=form_data)

        new_user = {
            'username': username,
            'password': password,
            'role': role
        }

        if role == 'player':
            if not age_range or not position:
                flash("Para jugadores, la edad y la posición son obligatorias", "error")
                return render_template('register.html', form_data=form_data)
            new_user['age_range'] = age_range
            new_user['position'] = position

        users.insert_one(new_user)
        flash("Registro exitoso", "success")
        return redirect(url_for('login'))

    return render_template('register.html', form_data={})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not users:
        flash("Base de datos no disponible", "error")
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        form_data = request.form.to_dict()

        user = users.find_one({'username': username, 'password': password})
        if user:
            session['username'] = username
            session['role'] = user.get('role')
            flash('Inicio de sesión exitoso', 'success')

            role = user.get('role')
            if role == 'player':
                return redirect(url_for('player'))
            elif role == 'coach':
                return redirect(url_for('coach'))
            elif role == 'recruiter':
                return redirect(url_for('recruiter'))
            else:
                flash("Rol desconocido", "error")
                return redirect(url_for('login'))
        else:
            flash('Credenciales incorrectas', 'error')
            return render_template('login.html', form_data=form_data)

    return render_template('login.html', form_data={})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/reset', methods=['GET', 'POST'])
def password_reset():
    if request.method == 'POST':
        flash("Si el usuario existe, se enviará un correo con instrucciones.", "info")
        return redirect(url_for('login'))
    return render_template('password_reset.html', form_data={})

@app.route('/player')
def player():
    if session.get('role') != 'player':
        return redirect(url_for('login'))

    username = session.get('username')
    user = users.find_one({'username': username}) if users else None
    feed = list(videos.find({'user': username, 'role': 'player'}).sort('timestamp', -1)) if videos else []
    return render_template('player.html', feed=feed, user=user)

@app.route('/coach')
def coach():
    if session.get('role') != 'coach':
        return redirect(url_for('login'))

    feed = list(videos.find({'role': 'player'}).sort('timestamp', -1)) if videos else []
    return render_template('coach.html', feed=feed)

@app.route('/recruiter')
def recruiter():
    if session.get('role') != 'recruiter':
        return redirect(url_for('login'))

    players_data = []
    if users:
        players_cursor = users.find({'role': 'player'})
        for player in players_cursor:
            players_data.append({
                'nombre': player.get('username', 'Jugador'),
                'posicion': player.get('position', 'No definida'),
                'edad': player.get('age_range', 'No definida')
            })

    return render_template('recruiter.html', players=players_data)

@app.route('/player_profile/<username>')
def player_profile(username):
    if session.get('role') != 'recruiter':
        return redirect(url_for('login'))

    player = users.find_one({'username': username})
    if not player:
        flash("Jugador no encontrado", "error")
        return redirect(url_for('recruiter'))

    # Mismo patrón que en /player
    feed = list(videos.find({'user': username, 'role': 'player'}).sort('timestamp', -1)) if videos else []

    return render_template('player_profile.html', player=player, feed=feed)

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'username' not in session:
        return redirect(url_for('login'))

    file = request.files.get('video')
    if not file:
        flash("No se seleccionó ningún archivo", "error")
        return redirect(request.referrer)

    try:
        result = cloudinary.uploader.upload_large(
            file.stream,
            resource_type="video"
        )

        if videos:
            videos.insert_one({
                "user": session['username'],
                "role": session['role'],
                "video_url": result['secure_url'],
                "timestamp": datetime.utcnow()
            })

        flash("Video subido con éxito", "success")
    except Exception as e:
        print("Error subiendo video a Cloudinary:", e, file=sys.stderr)
        flash("Error al subir el video", "error")

    return redirect(request.referrer)

if __name__ == '__main__':
    app.run(debug=True)
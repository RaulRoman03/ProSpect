from flask import Flask, render_template, request, redirect, session, url_for, flash
from pymongo import MongoClient, errors
from datetime import datetime
import os
import sys
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey")

MONGO_URI = os.environ.get("MONGO_URI")
cloud_name = os.environ.get("cloud_name")
api_key = os.environ.get("api_key")
api_secret = os.environ.get("api_secret")

users = None
videos = None

cloudinary.config( 
    cloud_name = cloud_name, 
    api_key = api_key, 
    api_secret = api_secret,
    secure=True
)

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    client.server_info()
    db = client.get_default_database()
    users = db.users
    videos = db.videos
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

    return render_template('register.html', form_data={})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        form_data = request.form.to_dict()

        user = users.find_one({'username': username, 'password': password, 'role': role})
        if user:
            session['username'] = username
            session['role'] = role
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for(role))
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

    feed = list(videos.find({'role': 'player'}).sort('timestamp', -1))
    return render_template('player.html', feed=feed)

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
            file,
            resource_type="video"
        )

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
from flask import Flask, render_template, request, redirect, session, url_for, flash
from pymongo import MongoClient, errors
from datetime import datetime
import os
import sys
import cloudinary.uploader

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get("SECRET_KEY", "miclave")

MONGO_URI = os.environ.get("MONGO_URI")
cloud_name = os.environ.get("cloud_name")
api_key = os.environ.get("api_key")
api_secret = os.environ.get("api_secret")

usuarios = None
videos = None

cloudinary.config(
    cloud_name=cloud_name,
    api_key=api_key,
    api_secret=api_secret,
    secure=True
)

try:
    cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    cliente.server_info()
    db = cliente.get_default_database()
    usuarios = db.users
    videos = db.media
except errors.ServerSelectionTimeoutError as e:
    print("ERROR: No se pudo conectar a MongoDB:", e, file=sys.stderr)


@app.route('/')
def inicio():
    return render_template('index.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if not usuarios:
        flash("Base de datos no disponible", "error")
        return redirect(url_for('inicio'))

    if request.method == 'POST':
        nombre = request.form.get('username')
        contraseña = request.form.get('password')
        rol = request.form.get('role')
        edad = request.form.get('age_range')
        posicion = request.form.get('position')
        datos = request.form.to_dict()

        if not nombre or not contraseña or not rol:
            flash("Todos los campos son obligatorios", "error")
            return render_template('register.html', form_data=datos)

        if rol not in ['player', 'coach', 'recruiter']:
            flash("Rol inválido", "error")
            return render_template('register.html', form_data=datos)

        if usuarios.find_one({'username': nombre}):
            flash("El usuario ya existe", "error")
            return render_template('register.html', form_data=datos)

        nuevo_usuario = {
            'username': nombre,
            'password': contraseña,
            'role': rol
        }

        if rol == 'player':
            if not edad or not posicion:
                flash("Edad y posición son obligatorias para jugadores", "error")
                return render_template('register.html', form_data=datos)
            nuevo_usuario['age_range'] = edad
            nuevo_usuario['position'] = posicion

        usuarios.insert_one(nuevo_usuario)
        flash("Registro exitoso", "success")
        return redirect(url_for('login'))

    return render_template('register.html', form_data={})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not usuarios:
        flash("Base de datos no disponible", "error")
        return redirect(url_for('inicio'))

    if request.method == 'POST':
        nombre = request.form['username']
        contraseña = request.form['password']
        datos = request.form.to_dict()

        usuario = usuarios.find_one({'username': nombre, 'password': contraseña})
        if usuario:
            session['username'] = nombre
            session['role'] = usuario.get('role')
            flash('Inicio de sesión exitoso', 'success')

            rol = usuario.get('role')
            if rol == 'player':
                return redirect(url_for('jugador'))
            elif rol == 'coach':
                return redirect(url_for('entrenador'))
            elif rol == 'recruiter':
                return redirect(url_for('reclutador'))
            else:
                flash("Rol desconocido", "error")
                return redirect(url_for('login'))
        else:
            flash('Credenciales incorrectas', 'error')
            return render_template('login.html', form_data=datos)

    return render_template('login.html', form_data={})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('inicio'))


@app.route('/reset', methods=['GET', 'POST'])
def restablecer():
    if request.method == 'POST':
        flash("Si el usuario existe, se enviará un correo con instrucciones.", "info")
        return redirect(url_for('login'))
    return render_template('password_reset.html', form_data={})


@app.route('/player')
def jugador():
    if session.get('role') != 'player':
        return redirect(url_for('login'))

    nombre = session.get('username')
    usuario = usuarios.find_one({'username': nombre}) if usuarios else None
    feed = list(videos.find({'user': nombre, 'role': 'player'}).sort('timestamp', -1)) if videos else []
    return render_template('player.html', feed=feed, user=usuario)


@app.route('/coach')
def entrenador():
    if session.get('role') != 'coach':
        return redirect(url_for('login'))

    feed = list(videos.find({'role': 'player'}).sort('timestamp', -1)) if videos else []
    return render_template('coach.html', feed=feed)


@app.route('/recruiter')
def reclutador():
    if session.get('role') != 'recruiter':
        return redirect(url_for('login'))

    filtro_posicion = request.args.get('position')
    filtro_edad = request.args.get('age_range')

    consulta = {'role': 'player'}
    if filtro_posicion:
        consulta['position'] = filtro_posicion
    if filtro_edad:
        consulta['age_range'] = filtro_edad

    jugadores = []
    if usuarios:
        for jugador in usuarios.find(consulta):
            jugadores.append({
                'username': jugador.get('username'),
                'position': jugador.get('position', 'No definida'),
                'age_range': jugador.get('age_range', 'No definida')
            })

    return render_template('recruiter.html', players=jugadores)


@app.route('/player/<username>')
def perfil_jugador(username):
    jugador = usuarios.find_one({'username': username, 'role': 'player'})
    if not jugador:
        flash("Jugador no encontrado", "error")
        return redirect(url_for('reclutador'))

    feed = list(videos.find({'user': username, 'role': 'player'}).sort('timestamp', -1)) if videos else []
    return render_template('player_profile.html', player=jugador, feed=feed)


@app.route('/subir_video', methods=['POST'])
def subir_video():
    if 'username' not in session:
        return redirect(url_for('login'))

    archivo = request.files.get('video')
    if not archivo:
        flash("No se seleccionó ningún archivo", "error")
        return redirect(request.referrer)

    try:
        resultado = cloudinary.uploader.upload_large(
            archivo.stream,
            resource_type="video"
        )

        if videos:
            videos.insert_one({
                "user": session['username'],
                "role": session['role'],
                "video_url": resultado['secure_url'],
                "timestamp": datetime.utcnow()
            })

        flash("Video subido con éxito", "success")
    except Exception as e:
        print("Error subiendo video a Cloudinary:", e, file=sys.stderr)
        flash("Error al subir el video", "error")

    return redirect(request.referrer)


if __name__ == '__main__':
    app.run(debug=True)
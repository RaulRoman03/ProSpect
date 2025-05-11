from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__, static_folder='ccs', template_folder='.')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/recruiter")
def recruiter():
    return render_template("recruiter.html")

@app.route("/player")
def player():
    return render_template("player.html")

@app.route("/coach")
def coach():
    return render_template("coach.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
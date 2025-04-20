from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
import os, json

app = Flask(__name__)
app.secret_key = 'super-secret-key'

CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/login", methods=["GET", "POST"])
def login():
    config = load_config()
    if request.method == "POST":
        if request.form["username"] == config["username"] and request.form["password"] == config["password"]:
            session["user"] = config["username"]
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    config = load_config()
    files = sorted(
        [f for f in os.listdir(config["recordings_path"]) if f.endswith(".wav")],
        key=lambda x: os.path.getmtime(os.path.join(config["recordings_path"], x)),
        reverse=True
    )
    return render_template("index.html", files=files)

@app.route("/voicemail")
def voicemail():
    if "user" not in session:
        return redirect(url_for("login"))
    config = load_config()
    voicemails = []
    for root, dirs, files in os.walk(config["voicemail_path"]):
        for file in files:
            if file.endswith(".wav"):
                relative_path = os.path.relpath(os.path.join(root, file), config["voicemail_path"])
                voicemails.append(relative_path)
    return render_template("voicemail.html", voicemails=voicemails)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user" not in session:
        return redirect(url_for("login"))

    config = load_config()

    if request.method == "POST":
        current_pass = request.form["current_password"]
        if current_pass != config["password"]:
            flash("Incorrect current password!", "error")
            return redirect(url_for("settings"))

        config["username"] = request.form["username"]
        config["password"] = request.form["new_password"]
        config["recordings_path"] = request.form["recordings_path"]
        config["voicemail_path"] = request.form["voicemail_path"]
        save_config(config)
        flash("Settings updated successfully!", "success")
        return redirect(url_for("settings"))

    return render_template("settings.html", config=config)

@app.route("/recordings/<filename>")
def download(filename):
    config = load_config()
    return send_from_directory(config["recordings_path"], filename)

@app.route("/voicemail_download/<path:filename>")
def voicemail_download(filename):
    config = load_config()
    return send_from_directory(config["voicemail_path"], filename)

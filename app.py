# app.py - Flask Website + Auto Start Telegram Bot
from flask import Flask, send_from_directory, request, render_template_string
import threading
import os
import subprocess

app = Flask(__name__)

# Auto Start Bot Jab Website Start Ho
def start_bot():
    print("Starting Telegram Bot...")
    subprocess.Popen(["python", "tg.py"])

# Start bot in background
threading.Thread(target=start_bot, daemon=True).start()

# === WEBSITE PAGES ===
@app.route("/")
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TeamDev.sbs - Website Mirror Bot</title>
        <style>
            body{font-family: 'Courier New';background:#000;color:#0f0;text-align:center;padding:50px;}
            h1{font-size:3em;text-shadow:0 0 10px #0f0;}
            .box{border:2px solid #0f0;padding:20px;margin:20px auto;max-width:600px;border-radius:10px;}
            a{color:#0f0;text-decoration:none;font-size:1.5em;}
        </style>
    </head>
    <body>
        <h1>╔═════◇◆◇═════╗</h1>
        <h1>TeamDev.sbs</h1>
        <h1>╚═════◇◆◇═════╝</h1>
        <div class="box">
            <h2>TeamDev</h2>
            <p>World's Most Powerful Website Mirror Bot</p>
            <p>5 Scrapes/Day • Cloud Links • Offline Ready</p>
            <br>
            <a href="https://t.me/Mirror_x_TeamDev_Robot">Open Bot</a>
        </div>
    </body>
    </html>
    """)

# === CLOUD DOWNLOAD SYSTEM ===
@app.route("/scraped/<path:filename>")
def download_scraped(filename):
    key = request.args.get("key")
    if not key:
        return "<h1>Access Denied</h1><p>No key provided, Go To t.me/Mirror_x_TeamDev_Robot</p>", 403
    
    file_path = os.path.join("scraped", filename)
    if not os.path.exists(file_path):
        return "<h1>404</h1><p>File not found, Go To t.me/Mirror_x_TeamDev_Robot</p>", 404
    
    # Simple key check (in real use database)
    key_file = file_path.replace(".zip", "") + "/key.txt"
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            real_key = f.read().strip()
        if key != real_key:
            return "<h1>Invalid Key, Go To t.me/Mirror_x_TeamDev_Robot</h1>", 403
    
    return send_from_directory("scraped", filename, as_attachment=True)

if __name__ == "__main__":
    print("TeamDev.sbs Website + Bot Started!")
    app.run(host="0.0.0.0", port=5000)

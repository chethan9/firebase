# app.py
import subprocess
import uuid
from flask import Flask, request, jsonify, send_file
from bs4 import BeautifulSoup
import requests
from werkzeug.utils import secure_filename
import os
import ffmpeg


def create_app():
    app = Flask(__name__, static_folder='uploads', static_url_path='/uploads')
    app.config['UPLOAD_FOLDER'] = '/app/uploads/'
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    # Other setup code...
    return app


app = create_app()


@app.route('/', methods=['GET'])
def homepage():
    return "Homepage"


@app.route('/hello', methods=['GET'])
def hello():
    return "Hello"


@app.route('/tor', methods=['GET'])
def tor():
    name = request.args.get('name')
    url = "https://2torrentz2eu.in/beta2/search.php?torrent-query=" + name
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Here you would write the code to parse the soup object and extract the data you need
    # For example, if the data is in a table, you might do something like this:
    table = soup.find('table')
    rows = table.find_all('tr')
    data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [col.text.strip() for col in cols]
        data.append(cols)
    return jsonify(data)

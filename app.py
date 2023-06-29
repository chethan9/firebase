# app.py
import subprocess
import uuid
from flask import Flask, request, jsonify, send_file, abort
from bs4 import BeautifulSoup
import requests
from werkzeug.utils import secure_filename
import os
import ffmpeg
import PTN


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
    try:
        name = request.args.get('name')
        url = "https://2torrentz2eu.in/beta2/search.php?torrent-query=" + name
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr')
        data = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 5:
                continue  # Skip rows with fewer than 5 td elements
            download_button = [col.find('button', class_='ui blue basic button') for col in cols]
            download_link = []
            for button in download_button:
                if button:
                    onclick_text = button.get('onclick')
                    link = onclick_text.split("'")[1]
                    full_link = "https://2torrentz2eu.in/beta2/page.php?url=" + link
                    download_link.append(full_link)
            # Remove empty strings from download_link
            download_link = [link for link in download_link if link]
            cols = [col.text.strip() for col in cols]
            # Create a dictionary for each row
            row_dict = {
                "Title": cols[0],
                "Seeds": int(cols[1]),
                "Leeches": int(cols[2]),
                "Size": cols[3],
                "Date": cols[4],
                "Download": download_link[0] if download_link else None
            }
            data.append(row_dict)
        return jsonify({"movies": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route('/magnet', methods=['GET'])
def magnet():
    url = request.args.get('url')
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Find the 'a' tag with class 'download-button' and id 'magnet'
    magnet_link_tag = soup.find('a', class_='download-button', id='magnet')
    if magnet_link_tag:
        magnet_link = magnet_link_tag.get('href')
        # Check if the link contains 'magnet:?xt='
        if 'magnet:?xt=' in magnet_link:
            return magnet_link
        else:
            return "Error: The link does not contain 'magnet:?xt='", 404
    else:
        return "Error: Could not find the 'Open Magnet' button", 404


@app.route('/parse', methods=['GET'])
def parse():
    filename = request.args.get('filename')
    info = PTN.parse(filename)
    return jsonify(info)

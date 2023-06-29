# app.py
import subprocess
import uuid
from flask import Flask, request, jsonify, send_file, abort, make_response
from bs4 import BeautifulSoup
import requests
from werkzeug.utils import secure_filename
import os
import ffmpeg
import PTN
import time

app = Flask(__name__)

def create_app():
    app = Flask(__name__, static_folder='uploads', static_url_path='/uploads')
    app.config['UPLOAD_FOLDER'] = '/app/uploads/'
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
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
        response = make_response(jsonify({"movies": data}), 200)
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
    except Exception as e:
        response = make_response(jsonify({"error": str(e)}), 500)
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


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
            return "Error: The link does not contain magnet", 404
    else:
        return "Error: Could not find the 'Open Magnet' button", 404


@app.route('/parse', methods=['GET'])
def parse():
    filename = request.args.get('filename')
    info = PTN.parse(filename)
    return jsonify(info)


@app.route('/movie', methods=['GET'])
def movie():
    try:
        # First, get the data from the /tor endpoint
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
        
        # Then, for each title in the data, parse it with the /parse functionality
        parsed_data = []
        for movie in data:
            title = movie['Title']
            parsed_title = PTN.parse(title)
            parsed_data.append(parsed_title)

        response = make_response(jsonify({"movies": parsed_data}), 200)
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
    except Exception as e:
        response = make_response(jsonify({"error": str(e)}), 500)
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

@app.route('/bolt', methods=['GET'])
def bolt():
    try:
        # First, get the data from the /tor endpoint
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
                "mainTitle": cols[0],
                "mainSeeds": int(cols[1]),
                "mainLeeches": int(cols[2]),
                "mainSize": cols[3],
                "mainDate": cols[4],
                "mainDownload": download_link[0] if download_link else None
            }
            data.append(row_dict)
        
        # Then, for each movie in the data, check for valid magnet links
        valid_data = []
        for movie in data:
            download_link = movie['mainDownload']
            if download_link:
                response = requests.get(download_link)
                soup = BeautifulSoup(response.text, 'html.parser')
                magnet_link_tag = soup.find('a', class_='download-button', id='magnet')
                if magnet_link_tag:
                    magnet_link = magnet_link_tag.get('href')
                    if 'magnet:?xt=' in magnet_link:
                        movie['mainDownload'] = magnet_link
                        valid_data.append(movie)
        
        # Finally, for each movie in valid_data, parse the title
        parsed_data = []
        for movie in valid_data:
            title = movie['mainTitle']
            parsed_title = PTN.parse(title)
            movie.update(parsed_title)
            parsed_data.append(movie)

        response = make_response(jsonify({"movies": parsed_data}), 200)
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
    except Exception as e:
        response = make_response(jsonify({"error": str(e)}), 500)
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


@app.route('/freebird', methods=['POST'])
def freebird():
    magnet_link = request.json.get('magnet_link')
    token = "6G7ZWHULQ7WXTTX6DD4CJKGA3OYY6F7HMXHYVL6JS6KXO3YSZAJQ"  # Replace with your actual token

    headers = {
        'Authorization': f'Bearer {token}'
    }

    # Step 1: Add Magnet
    response = requests.post('https://api.real-debrid.com/rest/1.0/torrents/addMagnet', headers=headers, data={'magnet': magnet_link})
    torrent_id = response.json()['id']

    # Step 2: Select Items to Download
    requests.post(f'https://api.real-debrid.com/rest/1.0/torrents/selectFiles/{torrent_id}', headers=headers, data={'files': 'all'})

    # Step 3: Fetch Torrent Info and wait for status to change to 'downloaded'
    while True:
        response = requests.get(f'https://api.real-debrid.com/rest/1.0/torrents/info/{torrent_id}', headers=headers)
        status = response.json()['status']
        if status == 'downloaded':
            break
        time.sleep(5)  # Wait for 5 seconds before checking again

    # Step 4: Get Download Links
    download_links = response.json()['links']
    final_links = []
    for link in download_links:
        response = requests.post('https://api.real-debrid.com/rest/1.0/unrestrict/link', headers=headers, data={'link': link})
        final_links.append(response.json()['download'])

    return jsonify({'download_links': final_links})

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
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote

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
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)
    query['url'] = [quote(query['url'][0], safe='')]  # URL-encode the value of the "url" query parameter
    encoded_url = urlunparse(parsed_url._replace(query=urlencode(query, doseq=True)))
    response = requests.get(encoded_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    magnet_link_tag = soup.find('a', class_='download-button', id='magnet')
    if magnet_link_tag:
        magnet_link = magnet_link_tag.get('href')
        if 'magnet:?xt=' in magnet_link:
            return jsonify({'magnet_link': magnet_link})
        else:
            return jsonify({'error': "The link does not contain magnet"}), 404
    else:
        return jsonify({'error': "Could not find the 'Open Magnet' button"}), 404

@app.route('/parse', methods=['GET'])
def parse():
    filename = request.args.get('filename')
    info = PTN.parse(filename)
    return jsonify(info)


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


@app.route('/tor2', methods=['GET'])
def tor2():
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
            seeds = int(cols[1].text.strip())
            if seeds == 0:
                continue  # Skip torrents with zero seeds
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
            if not download_link:
                continue  # Skip torrents without a download link
            # Get magnet link
            magnet_link_response = requests.get(download_link[0])
            magnet_soup = BeautifulSoup(magnet_link_response.text, 'html.parser')
            magnet_link_tag = magnet_soup.find('a', class_='download-button', id='magnet')
            if not magnet_link_tag or 'magnet:?xt=' not in magnet_link_tag.get('href'):
                continue  # Skip torrents without a magnet link
            cols = [col.text.strip() for col in cols]
            # Create a dictionary for each row
            row_dict = {
                "Title": cols[0],
                "Seeds": seeds,
                "Leeches": int(cols[2]),
                "Size": cols[3],
                "Date": cols[4],
                "Download": download_link[0]
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

@app.route('/movie', methods=['GET'])
def movie():
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
            seeds = int(cols[1].text.strip())
            if seeds == 0:
                continue  # Skip torrents with zero seeds
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
            title = cols[0]
            parsed_title = PTN.parse(title)  # Parse the title
            # Create a dictionary for each row
            row_dict = {
                "mTitle": title,
                "mSeeds": seeds,
                "mLeeches": int(cols[2]),
                "mSize": cols[3],
                "mDate": cols[4],
                "mDownload": download_link[0]
            }
            # Merge parsed title into row_dict
            row_dict.update(parsed_title)
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

@app.route('/1337', methods=['GET'])
def leet():
    try:
        name = request.args.get('name')
        url = "https://www.1377x.to/search/" + name + "/1/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr')
        data = []
        for row in rows[1:]:  # Skip the header row
            cols = row.find_all('td')
            seeds = int(cols[4].text)
            if seeds == 0:
                continue  # Skip torrents with zero seeds
            title_link = cols[0].find('a')
            title = title_link.text
            download_link = "https://www.1377x.to" + title_link.get('href')
            # Get magnet link
            magnet_response = requests.get(download_link)
            magnet_soup = BeautifulSoup(magnet_response.text, 'html.parser')
            magnet_link_tag = magnet_soup.find('a', href=lambda href: href and href.startswith('magnet:?'))
            if not magnet_link_tag:
                continue  # Skip torrents without a magnet link
            magnet_link = magnet_link_tag.get('href')
            # Create a dictionary for each row
            row_dict = {
                "Title": title,
                "Seeds": seeds,
                "Leeches": int(cols[5]),
                "Size": cols[1],  
                "Date": cols[3], 
                "Uploader": cols[6],
                "Download": download_link,
                "Magnet": magnet_link
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

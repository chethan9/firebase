from datetime import datetime, timedelta
import jwt
import os
import requests
import time
import uuid
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, make_response
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote
from werkzeug.utils import secure_filename
import PTN
import os
import logging
from flask import Flask, request, Response
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time


app = Flask(__name__)

# Get the current directory
current_directory = os.getcwd()

# Set the log file path in the root directory
log_file_path = os.path.join(current_directory, 'api.log')
# Configure logging
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_app():
    app = Flask(__name__, static_folder='uploads', static_url_path='/uploads')
    app.config['UPLOAD_FOLDER'] = '/app/uploads/'
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return app


app = create_app()

@app.before_request
def before_request():
    # This code will be executed before each request
    app.logger.info('Request: %s %s', request.method, request.url)
    app.logger.info('Headers: %s', request.headers)
    app.logger.info('Body: %s', request.get_data())


@app.after_request
def after_request(response):
    # This code will be executed after each request
    app.logger.info('Response: %s', response.status)
    return response

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
            seeds = int(cols[1].text.strip())
            if seeds == 0:
                continue  # Skip torrents with zero seeds
            title_link = cols[0].find('a', href=True, class_=False)  # Exclude the icon link
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
                "Leeches": int(cols[2].text.strip()),
                "Size": cols[4].text,  # Don't strip "Size"
                "Date": cols[3].text,  # Don't strip "Date"
                "Uploader": cols[5].text,
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


@app.route('/info', methods=['GET'])
def info():
    name = request.args.get('name')
    api_key = "0308f0a9278f09cbd10fe7441ccc6664"  # replace with your actual TMDB API key

    # Make API call to TMDB for movies
    movie_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={name}"
    movie_response = requests.get(movie_url)
    movie_data = movie_response.json()

    # Make API call to TMDB for TV shows
    tv_url = f"https://api.themoviedb.org/3/search/tv?api_key={api_key}&query={name}"
    tv_response = requests.get(tv_url)
    tv_data = tv_response.json()

    # Combine the results
    results = []
    for movie in movie_data.get('results', []):
        poster_path = movie.get('poster_path')
        if poster_path is None:
            poster_path = "https://i.ibb.co/72MHwtr/No-Image-Placeholder.jpg"
        else:
            poster_path = f"https://www.themoviedb.org/t/p/w94_and_h141_bestv2{poster_path}"
        results.append({
            'name': movie.get('title'),
            'poster_image_path': poster_path,
            'overview': movie.get('overview'),
            'release_date': movie.get('release_date'),
            'type': 'Movie',
            'popularity': movie.get('popularity', 0),
            'original_language': movie.get('original_language')
        })

    for tv_show in tv_data.get('results', []):
        poster_path = tv_show.get('poster_path')
        if poster_path is None:
            poster_path = "https://i.ibb.co/72MHwtr/No-Image-Placeholder.jpg"
        else:
            poster_path = f"https://www.themoviedb.org/t/p/w94_and_h141_bestv2{poster_path}"
        results.append({
            'name': tv_show.get('name'),
            'poster_image_path': poster_path,
            'overview': tv_show.get('overview'),
            'release_date': tv_show.get('first_air_date'),
            'type': 'TV Show',
            'popularity': tv_show.get('popularity', 0),
            'original_language': tv_show.get('original_language')
        })

    # Sort the results by popularity and prioritize items with images
    results.sort(key=lambda x: (x['poster_image_path'] == "https://i.ibb.co/72MHwtr/No-Image-Placeholder.jpg", -x['popularity']))

    return jsonify({'info': results})


@app.route('/zcreate', methods=['POST'])
def create_zoom_meeting():
    user_id = request.json.get('user_id')
    api_key = request.json.get('api_key')
    api_secret = request.json.get('api_secret')
    topic = request.json.get('topic')
    start_time = request.json.get('start_time')  # Expected format: '2023-07-21T10:00:00'
    duration = request.json.get('duration')  # Expected in minutes
    agenda = request.json.get('agenda')
    password = request.json.get('password')

    # Generate a JWT
    payload = {
        'iss': api_key,
        'exp': datetime.now() + timedelta(minutes=15)
    }
    token = jwt.encode(payload, api_secret, algorithm='HS256')

    # Create the meeting
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        'topic': topic,
        'type': 2,  # Scheduled meeting
        'start_time': start_time,
        'duration': duration,
        'timezone': 'Asia/Kuwait',
        'agenda': agenda,
        'password': password
    }
    response = requests.post(f'https://api.zoom.us/v2/users/{user_id}/meetings', headers=headers, json=data)

    # Return the meeting info
    return jsonify(response.json())

@app.route('/zupdate', methods=['PATCH'])
def update_zoom_meeting():
    meeting_id = request.json.get('meeting_id')
    api_key = request.json.get('api_key')
    api_secret = request.json.get('api_secret')
    topic = request.json.get('topic')
    start_time = request.json.get('start_time')  # Expected format: '2023-07-21T10:00:00'
    duration = request.json.get('duration')  # Expected in minutes
    agenda = request.json.get('agenda')
    password = request.json.get('password')

    # Generate a JWT
    payload = {
        'iss': api_key,
        'exp': datetime.now() + timedelta(minutes=15)
    }
    token = jwt.encode(payload, api_secret, algorithm='HS256')

    # Update the meeting
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        'topic': topic,
        'type': 2,  # Scheduled meeting
        'start_time': start_time,
        'duration': duration,
        'timezone': 'Asia/Kuwait',
        'agenda': agenda,
        'password': password
    }
    response = requests.patch(f'https://api.zoom.us/v2/meetings/{meeting_id}', headers=headers, json=data)

    # Check the response
    if response.status_code == 204:
        return '', 204
    else:
        return jsonify(response.json()), response.status_code

@app.route('/zinfo', methods=['GET'])
def get_zoom_meeting():
    meeting_id = request.args.get('meeting_id')
    api_key = request.args.get('api_key')
    api_secret = request.args.get('api_secret')

    # Generate a JWT
    payload = {
        'iss': api_key,
        'exp': datetime.now() + timedelta(minutes=15)
    }
    token = jwt.encode(payload, api_secret, algorithm='HS256')

    # Get the meeting info
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.get(f'https://api.zoom.us/v2/meetings/{meeting_id}', headers=headers)

    # Return the meeting info
    return jsonify(response.json())

@app.route('/logs', methods=['GET'])
def get_logs():
    start_date = request.args.get('start_date')  # Get the start date from query parameter
    end_date = request.args.get('end_date')  # Get the end date from query parameter

    # Check if both start date and end date are provided
    if start_date and end_date:
        logs = []
        with open(log_file_path, 'r') as file:
            for line in file:
                log_data = line.strip().split(' - ')
                log_timestamp = log_data[0]
                log_level = log_data[1]
                log_message = log_data[2]
                if start_date <= log_timestamp <= end_date:
                    logs.append({
                        'timestamp': log_timestamp,
                        'level': log_level,
                        'message': log_message
                    })
        return jsonify(logs)
    else:
        return 'Please provide both start_date and end_date query parameters.', 400



@app.route('/google-lens', methods=['GET'])
def google_lens():
    image_url = request.args.get('url')

    # Set up Firefox options for Selenium
    options = Options()
    options.headless = True  # Run Firefox in headless mode

    # Set up Selenium to use Firefox
    driver = webdriver.Firefox(options=options, executable_path='/var/lib/data/geckodriver')

    # Visit the Google Lens page and input the image URL
    driver.get(f'https://lens.google.com/uploadbyurl?url={image_url}')

    # Wait for the page to load and the results to appear
    # This may require more sophisticated waiting logic in practice
    time.sleep(5)

    # Get the page HTML
    page_html = driver.page_source

    # Close the Selenium driver
    driver.quit()

    return Response(page_html, mimetype='text/html')

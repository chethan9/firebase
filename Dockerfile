# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Set the working directory in the container to /app
WORKDIR /app

# FFmpeg, Firefox, and geckodriver installation
RUN apt-get update && \
    apt-get install -y ffmpeg firefox-esr wget unzip && \
    mkdir -p /var/lib/data && \
    wget https://github.com/mozilla/geckodriver/releases/download/v0.29.1/geckodriver-v0.29.1-linux64.tar.gz -P /var/lib/data && \
    tar -xvzf /var/lib/data/geckodriver-v0.29.1-linux64.tar.gz -C /var/lib/data && \
    rm /var/lib/data/geckodriver-v0.29.1-linux64.tar.gz && \
    chmod +x /var/lib/data/geckodriver && \
    ln -s /var/lib/data/geckodriver /usr/local/bin/geckodriver && \
    apt-get remove -y wget unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add current directory files to /app in container
ADD . /app

# Install necessary packages, Flask, BeautifulSoup, requests, ffmpeg-python, gunicorn, parse-torrent-title, pyjwt, selenium, cinemagoer, jsmin, css_html_js_minify
RUN pip install --no-cache-dir flask werkzeug beautifulsoup4 requests ffmpeg-python gunicorn parse-torrent-title pyjwt selenium cinemagoer jsmin css_html_js_minify cssutils htmlmin instaloader instagrapi Pillow>=8.1.1

# Run app.py (Flask server) when the container launches
CMD gunicorn --bind 0.0.0.0:$PORT app:app

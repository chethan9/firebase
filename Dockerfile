# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# FFmpeg installation
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install Firefox
RUN apt-get update && \
    apt-get install -y firefox-esr && \
    rm -rf /var/lib/apt/lists/*

# Install geckodriver
RUN apt-get update && \
    apt-get install -y wget unzip && \
    mkdir -p /var/lib/data && \
    wget https://github.com/mozilla/geckodriver/releases/download/v0.29.1/geckodriver-v0.29.1-linux64.tar.gz -P /var/lib/data && \
    tar -xvzf /var/lib/data/geckodriver-v0.29.1-linux64.tar.gz -C /var/lib/data && \
    rm /var/lib/data/geckodriver-v0.29.1-linux64.tar.gz && \
    chmod +x /var/lib/data/geckodriver && \
    ln -s /var/lib/data/geckodriver /usr/local/bin/geckodriver && \
    apt-get remove -y wget unzip && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container to /app
WORKDIR /app

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Add current directory files to /app in container
ADD . /app

# Install necessary packages, Flask, BeautifulSoup, requests, ffmpeg-python, gunicorn, parse-torrent-title, pyjwt, selenium, cinemagoer, jsmin, css_html_js_minify
RUN pip install --no-cache-dir flask werkzeug beautifulsoup4 requests ffmpeg-python gunicorn parse-torrent-title pyjwt selenium cinemagoer jsmin css_html_js_minify htmlmin

# Make port 5000 available to the world outside this container
# EXPOSE 5000

# Run app.py (Flask server) when the container launches
CMD gunicorn --bind 0.0.0.0:$PORT app:app

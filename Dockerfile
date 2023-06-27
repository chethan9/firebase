# Use an official Python runtime as a parent image
FROM python:3.7-slim

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into theApologies for the abrupt cut-off. Here's the continuation and completion of the Dockerfile:

```Dockerfile
# Add the current directory contents into the container at /app
ADD . /app

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV API_KEY=c113b60e41eca7474dcc993fb4a8  # Replace with your actual API key

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run app.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]

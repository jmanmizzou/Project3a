# Use an official Python image as the base image
FROM python:3.8-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the contents of the current directory into the container's /app directory
COPY . /app

# Upgrade pip
RUN pip install --upgrade pip

# Install any required packages listed in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set the default command to run when starting the container
CMD ["python", "app.py"]

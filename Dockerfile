# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose a port (this is mostly informational in Docker; Heroku will provide the PORT env variable)
EXPOSE 5000

# Run the application using Uvicorn,
# using the dynamic PORT provided by Heroku (default to 5000 for local testing)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-5000}

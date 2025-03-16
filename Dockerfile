# Use an official lightweight Python image.
FROM python:3.9-slim

# Set the working directory in the container.
WORKDIR /app

# Install dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code.
COPY . .

# Expose port 80 for the application.
EXPOSE 80

# Run the FastAPI application with uvicorn.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

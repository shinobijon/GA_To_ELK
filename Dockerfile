# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Copy project files
COPY ga4_export.py .
COPY .env.example .

# Install dependencies
RUN pip install --no-cache-dir elasticsearch google-analytics-data

# Run the script
ENTRYPOINT [ "python", "ga4_export.py" ]

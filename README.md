# Google Analytics to Elasticsearch Exporter

This project fetches Google Analytics 4 (GA4) data and exports it to an Elasticsearch instance. It is designed to run inside a Docker container and connects to GA4 via a Google Service Account.

## Features

- Authenticates with GA4 using a service account JSON key
- Pulls GA4 metrics and dimensions via Google Analytics Data API
- Sends data to Elasticsearch with proper timestamp formatting
- Supports configuration via environment variables
- Runs inside an isolated Docker container

## Setup Instructions

1. **Google Cloud Setup**

   - Create or select a Google Cloud project.
   - Enable the **Google Analytics Data API**.
   - Create a **Service Account** and download the JSON key.
   - Give the service account **Read & Analyze** access to your GA4 property.

2. **Prepare Environment**

   - Copy `.env.example` to `.env`
   - Edit `.env` with your actual values:
     - GA4 Property ID
     - Path to your service account JSON key (mounted as `/app/service-account.json` in Docker)
     - Elasticsearch URL and API key

3. **Run the exporter**

Use Docker to run the export:

```bash
docker run --rm \
  --env-file .env \
  -v $(pwd):/app \
  -w /app \
  python:3.13.0 \
  sh -c "pip install elasticsearch google-analytics-data && python ga4_export.py"
```
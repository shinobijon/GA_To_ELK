import os
import logging
import datetime
from datetime import datetime, timedelta

from elasticsearch import Elasticsearch
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
from google.oauth2 import service_account

# Logging Setup
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load Environment Variables
GA_PROPERTY_ID = os.getenv("GA_PROPERTY_ID")
GA_CREDENTIALS_PATH = os.getenv("GA_CREDENTIALS_PATH")
GA_DAYS_TO_PULL = int(os.getenv("GA_DAYS_TO_PULL", "30"))
GA_REPORT_LIMIT = int(os.getenv("GA_REPORT_LIMIT", "100000"))
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API_KEY")

def validate_config():
    if not GA_PROPERTY_ID:
        logger.error("GA_PROPERTY_ID environment variable is not set. Exiting.")
        exit(1)
    if not GA_CREDENTIALS_PATH or not os.path.exists(GA_CREDENTIALS_PATH):
        logger.error(f"GA Service Account credentials file not found at: {GA_CREDENTIALS_PATH}. Exiting.")
        exit(1)
    if not ELASTICSEARCH_HOST:
        logger.error("ELASTICSEARCH_HOST environment variable not set. Exiting.")
        exit(1)

def main():
    validate_config()

    # Authenticate Google Analytics client
    try:
        credentials = service_account.Credentials.from_service_account_file(GA_CREDENTIALS_PATH)
        ga_client = BetaAnalyticsDataClient(credentials=credentials)
        logger.info("Authenticated to Google Analytics.")
    except Exception as e:
        logger.error(f"Failed to authenticate to Google Analytics: {e}")
        exit(1)

    # Prepare GA4 report request
    end_date = datetime.today()
    start_date = end_date - timedelta(days=GA_DAYS_TO_PULL)

    request = RunReportRequest(
        property=f"properties/{GA_PROPERTY_ID}",
        dimensions=[Dimension(name="date"), Dimension(name="pagePath")],
        metrics=[Metric(name="screenPageViews"), Metric(name="sessions")],
        date_ranges=[DateRange(start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))],
        limit=GA_REPORT_LIMIT
    )

    # Fetch report data
    try:
        response = ga_client.run_report(request)
        logger.info(f"Pulled {len(response.rows)} GA rows from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}.")
    except Exception as e:
        logger.error(f"Failed to fetch GA report: {e}")
        exit(1)

    # Connect Elasticsearch
    try:
        es = Elasticsearch(
            ELASTICSEARCH_HOST,
            api_key=ELASTICSEARCH_API_KEY,
            verify_certs=False  # Use only if self hosting ssl certificates as it disables SSL cert validation. If using normal SSL, then change to True
        )
        if not es.ping():
            raise Exception("Elasticsearch server not responding")
        logger.info("Connected to Elasticsearch.")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {e}")
        exit(1)

    # Send GA data to Elasticsearch
    try:
        for row in response.rows:
            doc = {dim.name: val.value for dim, val in zip(response.dimension_headers, row.dimension_values)}
            doc.update({metric.name: float(val.value or 0) for metric, val in zip(response.metric_headers, row.metric_values)})
            doc['@timestamp'] = datetime.datetime.utcnow().isoformat()

            es.index(index="ga4-data", document=doc)

        logger.info("Successfully sent GA data to Elasticsearch index: ga4-data")
    except Exception as e:
        logger.error(f"Failed to send data to Elasticsearch: {e}")
        exit(1)

if __name__ == "__main__":
    main()

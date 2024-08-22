import os
import sqlite3
import logging
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load AWS credentials from environment variables
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'ap-south-1')

# S3 Bucket configuration
S3_BUCKET_NAME = 'my-beest-db'
DB_FILE_NAME = 'orders_test.db'

# Initialize the S3 client
logging.debug(f"Using AWS region: {AWS_DEFAULT_REGION}")

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

def validate_s3_access():
    """Validate access to the S3 bucket."""
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME)
        if 'Contents' in response:
            logging.info(f"Successfully accessed S3 bucket {S3_BUCKET_NAME}.")
        else:
            logging.warning(f"S3 bucket {S3_BUCKET_NAME} is empty or not accessible.")
    except ClientError as e:
        logging.error(f"Failed to access S3 bucket {S3_BUCKET_NAME}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error occurred while accessing S3 bucket: {e}")

def download_db_from_s3():
    """Download the SQLite database from S3."""
    try:
        logging.debug("Starting download of the database from S3...")
        s3_client.download_file(S3_BUCKET_NAME, DB_FILE_NAME, DB_FILE_NAME)
        logging.info(f"Database {DB_FILE_NAME} downloaded from S3 bucket {S3_BUCKET_NAME}.")
    except (NoCredentialsError, PartialCredentialsError) as e:
        logging.error(f"Credentials error during S3 download: {e}")
    except ClientError as e:
        logging.error(f"Failed to download {DB_FILE_NAME} from S3 bucket: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during S3 download: {e}")

def init_db():
    """Initialize SQLite database and validate S3 access."""
    try:
        conn = sqlite3.connect(DB_FILE_NAME)
        c = conn.cursor()
        # Create test table if it does not exist
        c.execute('''CREATE TABLE IF NOT EXISTS test_table
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      test_column TEXT)''')
        conn.commit()
        conn.close()
        logging.debug("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"SQLite error occurred during initialization: {e}")

def insert_test_data():
    """Insert test data into the SQLite database."""
    try:
        conn = sqlite3.connect(DB_FILE_NAME)
        c = conn.cursor()
        # Insert test data
        c.execute("INSERT INTO test_table (test_column) VALUES ('Test Data')")
        conn.commit()
        conn.close()
        logging.info("Test data inserted successfully.")
    except sqlite3.Error as e:
        logging.error(f"SQLite error occurred while inserting data: {e}")

def upload_db_to_s3():
    """Upload the SQLite database to S3."""
    try:
        logging.debug("Starting upload of the database to S3...")
        s3_client.upload_file(DB_FILE_NAME, S3_BUCKET_NAME, DB_FILE_NAME)
        logging.info(f"Database {DB_FILE_NAME} uploaded to S3 bucket {S3_BUCKET_NAME}.")
    except (NoCredentialsError, PartialCredentialsError) as e:
        logging.error(f"Credentials error during S3 upload: {e}")
    except ClientError as e:
        logging.error(f"Failed to upload {DB_FILE_NAME} to S3 bucket: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during S3 upload: {e}")

if __name__ == '__main__':
    # Validate S3 access before starting
    validate_s3_access()

    # Download the database from S3 before starting
    download_db_from_s3()

    # Initialize the database (creates a table if it doesn't exist)
    init_db()

    # Insert test data into the database
    insert_test_data()

    # Upload the updated database back to S3
    upload_db_to_s3()

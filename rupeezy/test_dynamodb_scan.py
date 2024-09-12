import boto3
import logging
from decimal import Decimal
from botocore.exceptions import ClientError

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize the DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('StockEligibility')

def scan_all_dynamodb_table():
    """Scan and log all items in the table."""
    try:
        # Scan the DynamoDB table and print all items
        response = table.scan()
        items = response.get('Items', [])
        if items:
            logging.info(f"Found {len(items)} total items:")
            for item in items:
                logging.info(f"Item: {item}")
        else:
            logging.info("No items found in the table.")
    except ClientError as e:
        logging.error(f"Error scanning DynamoDB table: {e}")
        return None

def scan_filtered_by_status():
    """Scan the table filtering by EligibilityStatus = 'Eligible'."""
    try:
        # Scan the table for stocks that are eligible
        response = table.scan(
            FilterExpression="EligibilityStatus = :status",
            ExpressionAttributeValues={
                ':status': {'S': 'Eligible'}
            }
        )
        items = response.get('Items', [])
        if items:
            logging.info(f"Found {len(items)} items matching 'Eligible' status:")
            for item in items:
                logging.info(f"{item['InstrumentName']['S']} - EligibilityStatus: {item['EligibilityStatus']['S']}")
        else:
            logging.info("No matching items found.")
    except ClientError as e:
        logging.error(f"Error scanning DynamoDB table: {e}")
        return None

def scan_filtered_by_quantity():
    """Scan the table filtering by AdditionalQuantity > 0."""
    try:
        # Scan the table for stocks that have AdditionalQuantity > 0
        response = table.scan(
            FilterExpression="AdditionalQuantity > :qty",
            ExpressionAttributeValues={
                ':qty': Decimal('0')
            }
        )
        items = response.get('Items', [])
        if items:
            logging.info(f"Found {len(items)} items with AdditionalQuantity > 0:")
            for item in items:
                logging.info(f"{item['InstrumentName']['S']} - AdditionalQuantity: {item['AdditionalQuantity']['N']}")
        else:
            logging.info("No matching items found.")
    except ClientError as e:
        logging.error(f"Error scanning DynamoDB table: {e}")
        return None

def scan_filtered_dynamodb_table():
    """Scan the table filtering by both EligibilityStatus = 'Eligible' and AdditionalQuantity > 0."""
    try:
        # Scan the table for stocks that are eligible and have AdditionalQuantity > 0
        response = table.scan(
            FilterExpression="EligibilityStatus = :status AND AdditionalQuantity > :qty",
            ExpressionAttributeValues={
                ':status': {'S': 'Eligible'},
                ':qty': Decimal('0')
            }
        )
        # Print out the matching items
        items = response.get('Items', [])
        if items:
            logging.info(f"Found {len(items)} matching items:")
            for item in items:
                logging.info(f"{item['InstrumentName']['S']} - AdditionalQuantity: {item['AdditionalQuantity']['N']}")
        else:
            logging.info("No matching items found.")
    except ClientError as e:
        logging.error(f"Error scanning DynamoDB table: {e}")
        return None

if __name__ == "__main__":
    logging.info("Starting full table scan...")
    scan_all_dynamodb_table()  # First scan all items in the table
    
    logging.info("Starting filter by EligibilityStatus...")
    scan_filtered_by_status()  # Test EligibilityStatus filter
    
    logging.info("Starting filter by AdditionalQuantity...")
    scan_filtered_by_quantity()  # Test AdditionalQuantity filter
    
    logging.info("Starting combined filter...")
    scan_filtered_dynamodb_table()  # Test combined filter

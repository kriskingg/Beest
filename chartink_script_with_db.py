import os
import requests
from bs4 import BeautifulSoup
import logging
from time import sleep
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Constants for Chartink
Charting_Link = "https://chartink.com/screener/"
Charting_url = 'https://chartink.com/screener/process'
condition = "( {166311} ( latest rsi(65) < latest ema(rsi(65),35) or weekly rsi(65) < weekly ema(rsi(65),35) ) )"

# Load API Key from environment variables
YOUR_API_KEY = os.getenv('YOUR_API_KEY')

def get_access_token():
    """Read access token from the file."""
    try:
        with open('./token/access_token.txt', 'r') as file:
            token = file.read().strip()
            if token:
                logging.debug(f"Access token retrieved: '{token}'")
            else:
                logging.error("Access token is empty.")
            return token
    except FileNotFoundError:
        logging.error("access_token.txt file not found.")
        return None
    except Exception as e:
        logging.error(f"Error reading access token: {e}")
        return None

def fetch_chartink_data(condition):
    """Fetch data from Chartink based on the given condition."""
    retries = 3
    for attempt in range(retries):
        try:
            with requests.Session() as s:
                s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
                logging.debug("Headers: {}".format(s.headers))
                r = s.get(Charting_Link)
                logging.debug("GET request to Charting_Link status code: {}".format(r.status_code))
                soup = BeautifulSoup(r.text, "html.parser")
                csrf_token = soup.select_one("[name='csrf-token']")['content']
                s.headers.update({'x-csrf-token': csrf_token})
                logging.debug("CSRF Token: {}".format(csrf_token))
                logging.debug("Scan Condition: {}".format(condition))
                response = s.post(Charting_url, data={'scan_clause': condition})
                logging.debug("POST request to Charting_url status code: {}".format(response.status_code))
                logging.debug("Request Data: {}".format({'scan_clause': condition}))
                response_json = response.json()
                logging.debug("Response JSON: {}".format(response_json))
                if response.status_code == 200:
                    return response_json
                else:
                    logging.error("Failed to fetch data with status code: {}".format(response.status_code))
        except Exception as e:
            logging.error("Exception during data fetch: {}".format(str(e)))
        sleep(10)  # wait before retrying
    logging.error("All retries failed")
    return None

def fetch_ltp_from_rupeezy(token):
    """Fetch LTP from Rupeezy for the given token."""
    api_url = f"https://vortex.trade.rupeezy.in/data/quote?q=NSE_EQ-{token}&mode=full"
    access_token = get_access_token()
    if not access_token:
        logging.error("Access token is not available.")
        return None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        logging.debug("Rupeezy LTP response: %s", response_json)

        # Try different keys and approaches to find the LTP
        ltp_1 = response_json.get('data', {}).get(f'NSE_EQ-{token}', {}).get('last_trade_price')
        ltp_2 = response_json.get('data', {}).get(f'NSE_EQ-{token}', {}).get('close_price')
        ltp_3 = response_json.get('data', {}).get(f'NSE_EQ-{token}', {}).get('depth', {}).get('sell', [])[0].get('price') if response_json.get('data', {}).get(f'NSE_EQ-{token}', {}).get('depth', {}).get('sell') else None
        
        logging.debug(f"LTP Possibilities: ltp_1={ltp_1}, ltp_2={ltp_2}, ltp_3={ltp_3}")
        
        # Return the first non-None LTP found
        return ltp_1 or ltp_2 or ltp_3

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching LTP: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred while fetching LTP: {err}")

    return None

def trigger_order_on_rupeezy(order_details, retries=10):
    """Trigger an order on Rupeezy with retry logic."""
    api_url = "https://vortex.trade.rupeezy.in/orders/regular"
    access_token = get_access_token()
    if not access_token:
        logging.error("Access token is not available.")
        return None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    for attempt in range(retries):
        logging.debug(f"Order attempt {attempt + 1} with price: {order_details['price']}")

        try:
            response = requests.post(api_url, json=order_details, headers=headers)
            response.raise_for_status()
            response_json = response.json()
            logging.debug("Order response: %s", response_json)

            if response_json.get('status') == 'success':
                return response_json
            else:
                logging.error(f"Order failed on attempt {attempt + 1}: {response_json}")
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred during order attempt {attempt + 1}: {http_err}")
        except Exception as err:
            logging.error(f"Other error occurred during order attempt {attempt + 1}: {err}")

        sleep(2)  # Short delay before retrying

    logging.error("All retries for order placement failed.")
    return None

if __name__ == '__main__':
    # Fetch data from Chartink
    data = fetch_chartink_data(condition)

    if data:
        alpha_data = [item for item in data['data'] if item['nsecode'] == 'ALPHA']
        
        if alpha_data:
            logging.debug(f"Filtered ALPHA data: {alpha_data}")
            
            # Get the current price from the Chartink data directly
            current_price = alpha_data[0]['close']
            logging.debug(f"LTP from Chartink data for ALPHA: {current_price}")

            # Fetch LTP from Rupeezy as well
            rupeezy_ltp = fetch_ltp_from_rupeezy(7412)
            logging.debug(f"LTP from Rupeezy data for ALPHA: {rupeezy_ltp}")
            
            # Use Rupeezy LTP if available, otherwise fall back to Chartink LTP
            ltp_to_use = rupeezy_ltp if rupeezy_ltp else current_price
            
            order_quantity = 1  # Default quantity
            
            order_details = {
                "exchange": "NSE_EQ",
                "token": 7412,  # Token number for ALPHA.
                "symbol": "ALPHA",
                "transaction_type": "BUY",
                "product": "DELIVERY",
                "variety": "RL",
                "quantity": order_quantity,
                "price": ltp_to_use,
                "trigger_price": 0.00,
                "disclosed_quantity": 0,
                "validity": "DAY",
                "validity_days": 1,
                "is_amo": False
            }
            
            response = trigger_order_on_rupeezy(order_details)
            if response and response.get('status') == 'success':
                order_id = response['data'].get('orderId')
                logging.info(f"Order executed successfully with ID: {order_id}")
            else:
                logging.error(f"Failed to place order. Response: {response}")
        else:
            logging.info("No ALPHA data found in Chartink results. No action taken.")
    else:
        logging.error("Failed to fetch data from Chartink.")

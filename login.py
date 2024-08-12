import requests
import os
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def login_and_save_token():
    try:
        # Ensure all necessary environment variables are set
        totp = os.getenv('TOTP')
        api_key = os.getenv('YOUR_API_KEY')
        client_code = os.getenv('YOUR_CLIENT_CODE')
        password = os.getenv('YOUR_PASSWORD')
        application_id = os.getenv('YOUR_APPLICATION_ID')

        if not totp or not api_key or not client_code or not password or not application_id:
            raise ValueError("One or more required environment variables are not set.")

        logging.info(f"Using TOTP: {totp}")

        # Prepare the request
        url = "https://vortex.trade.rupeezy.in/user/login"
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        data = {
            "client_code": client_code,
            "password": password,
            "totp": totp,
            "application_id": application_id
        }

        # Perform the login request
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Process the response
        response_data = response.json()
        access_token = response_data.get('data', {}).get('access_token')
        if response.status_code == 200 and access_token:
            logging.info(f"ACCESS_TOKEN={access_token}")
            # Save the access token to a file
            with open("access_token.txt", "w") as file:
                file.write(access_token)
        else:
            logging.error("Login failed or access token not found.")
            logging.error("Response data: %s", response_data)

    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP error occurred: {e}")
    except ValueError as ve:
        logging.error(f"Value error: {ve}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    login_and_save_token()

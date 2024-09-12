""" Get the current water usage from the local utility provider. """
import os

import requests
from dotenv import load_dotenv


def create_utility_provider_session(session):
    """Create a PHP session with the local utility provider.

    Args:
        session (requests.Session): A requests session object.

    Returns:
        None
    """
    utility_url = "https://utilitybilling.newberryfl.gov/utility/"
    session.request('GET', utility_url, timeout=15)


def authenticate_utility_provider_session(session, auth: dict) -> bool:
    """Authenticate the session with the local utility provider.

    Args:
        session (requests.Session): A requests session object.
        auth (dict): username and password for the local utility provider

    Returns:
        bool: True if the authentication was successful, False otherwise.
    """
    utility_url = "https://utilitybilling.newberryfl.gov/citizenlink/common/common/ajax/checkLoginCredentials.php"
    form_data = {
        "loginId": auth["username"],
        "passId": auth["password"],
        "SITENAME": "UTILITY",
        "timeout": 60,
        "linkAccount": 0,
        "accessLevel": 11,
        "widgetName": "INITIAL",
    }
    response = session.request('POST', utility_url, data=form_data, timeout=15)

    # Check if the JSON response.errors list is empty, or if the auth failed
    if len(response.json()["errors"]) == 0:
        return True

    return False


def get_jwt_token_from_utility_provider(session) -> str | None:
    """Get the JWT token from the local utility provider for use with the 3rd party API.

    Args:
        session (requests.Session): A requests session object

    Returns:
        str | None: The JWT token if successful, None otherwise.
    """
    # utility_url = "https://utilitybilling.newberryfl.gov/citizenlink/ubs/common/ajax/sensusFetchNewOAuthToken.php"
    utility_url = "https://utilitybilling.newberryfl.gov/citizenlink/ubs/common/ajax/sensusFetchClientAuthorization.php"
    form_data = {
        "SITENAME": "UTILITY",
        "timeout": 60,
        "linkAccount": 0,
    }
    response = session.request('POST', utility_url, data=form_data, timeout=15)
    if "access_token" not in response.json():
        return None
    else:
        return response.json()["access_token"]


def init_data_vendor_session(session, jwt_token: str) -> bool:
    """Get the cookies from the data vendor for use with the 3rd party API.

    Args:
        session (requests.Session): A requests session object
        jwt_token (str): JWT token from the local utility provider

    Returns:
        dict | None: A dictionary of cookies if successful, None otherwise.
    """
    data_vendor_url = "https://my-nwbry.sensus-analytics.com/init/init"
    payload = {
    }
    params = {
        "sso_auth": jwt_token,
    }
    headers = {
        "Content-Type": "application/json, charset=UTF-8",
        "Accept": "application/json, text/javascript, */*",
        "Origin": "https://my-nwbry.sensus-analytics.com"
    }
    response = session.request('POST', data_vendor_url, params=params, headers=headers, timeout=15, json=payload)
    cookies = response.cookies.get_dict()

    if "JSESSIONID" not in cookies:
        return False

    return True


def get_account_details(session, cookies: dict):

    data_vendor_url = "https://my-nwbry.sensus-analytics.com/account/details"
    response = requests.get(data_vendor_url, cookies=cookies, timeout=15)
    account_details = response.json()
    if not account_details:
        return None

    return cookies, account_details


def get_meters_by_type(session, jwt_token: str, account_number: str, meter_type: str) -> tuple | None:
    data_vendor_url = "https://my-nwbry.sensus-analytics.com/account/details"
    params = {
        "sso_auth": jwt_token,
    }
    data = {
        "accountNumber": account_number,
        "meterTypeByValue": meter_type
    }
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': f"https://my-nwbry.sensus-analytics.com/main.html?sso_auth={jwt_token}",
        'Origin': 'https://my-nwbry.sensus-analytics.com',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json; charset=UTF-8',
    }
    response = session.request('POST', data_vendor_url, json=data, headers=headers, params=params, timeout=15)
    response_json = response.json()
    if response_json.get('operationSuccess') is not True:
        return None

    meters = []
    if len(response_json.get('deviceIdList')) > 0:
        for meter_id in response_json.get('deviceIdList'):
            meters.append({
                "meterId": meter_id,
                "meterType": meter_type,
                "meterAddress": response_json.get('devices').get(meter_id).get('address').get('line1'),
            })
            if response_json.get('devices').get(meter_id).get('address').get('line2'):
                meters[-1]["meterAddress"] += f" {response_json.get('devices').get(meter_id).get('address').get('line2')}"
    if len(meters) == 0:
        return None
    return meters


def main():
    """Program entry point.
    """
    # Load the ENV file
    load_dotenv()

    local_utility_auth: dict = {
        "username": os.getenv("UTILITY_USERNAME"),
        "password": os.getenv("UTILITY_PASSWORD"),
        "account_number": os.getenv("ACCOUNT_NUMBER"),
    }

    # Create a requests session to store cookies
    session = requests.Session()

    # Generate the needed cookies for the local utility (PHPSESSID, UTILITY)
    print("Creating a session with the local utility provider...")
    create_utility_provider_session(session)

    # Authenticate the session with the local utility
    print("Authenticating with supplied username and password...")
    session_authenticated = authenticate_utility_provider_session(
        session, local_utility_auth
    )
    if not session_authenticated:
        print("Failed to authenticate with the local utility provider.")
        return

    # Get the JWT token from the local utility provider
    print("Getting JWT token for AMI portal from the local utility provider...")
    jwt_token = get_jwt_token_from_utility_provider(session)
    if not jwt_token:
        print("Failed to get the JWT token from the local utility provider.")
        return

    # Get the session cookies from the data vendor using the JWT token
    print("Starting session with AMI portal using token...")
    data_vendor_cookies = init_data_vendor_session(session, jwt_token)
    if not data_vendor_cookies:
        print("Failed to get the cookies from the data vendor.")
        return

    # Get the account details from the data vendor
    # account_details = get_account_details(data_vendor_cookies)
    for meter_type in ['water', 'electric', 'gas']:
        print(f"Getting all {meter_type} meters on account {local_utility_auth.get('account_number')}...")
        meters = get_meters_by_type(session, jwt_token, local_utility_auth.get('account_number'), meter_type)
        if not meters:
            print(f"\t- No meters of type {meter_type} found on the account.")
            continue
        print(f"\t- Found {len(meters)} meters of type {meter_type} on the account.")
        for meter in meters:
            print(f"\t\t- Meter ID: {meter['meterId']}")
            print(f"\t\t- Meter Address: {meter['meterAddress']}")
            print("\n")




if __name__ == "__main__":
    main()

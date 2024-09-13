"""Get the current meters on the AMI account from the local utility provider."""

import os
from logging import Logger, getLogger, StreamHandler
import json

import argparse
import requests
from dotenv import load_dotenv

LOGGER: Logger = getLogger(__name__)


def create_utility_provider_session(session):
    """Create a PHP session with the local utility provider.

    Args:
        session (requests.Session): A requests session object.

    Returns:
        None
    """
    utility_url = "https://utilitybilling.newberryfl.gov/utility/"
    session.request("GET", utility_url, timeout=15)


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
    response = session.request("POST", utility_url, data=form_data, timeout=15)

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
    response = session.request("POST", utility_url, data=form_data, timeout=15)
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
    payload = {}
    params = {
        "sso_auth": jwt_token,
    }
    headers = {
        "Content-Type": "application/json, charset=UTF-8",
        "Accept": "application/json, text/javascript, */*",
        "Origin": "https://my-nwbry.sensus-analytics.com",
    }
    response = session.request(
        "POST",
        data_vendor_url,
        params=params,
        headers=headers,
        timeout=15,
        json=payload,
    )
    cookies = response.cookies.get_dict()

    if "JSESSIONID" not in cookies:
        return False

    return True


def get_meters_by_type(
    session, jwt_token: str, account_number: str, meter_type: str
) -> dict | None:
    """Get the meters on the account by type.

    Args:
        session (requests.Session): Requests session object
        jwt_token (str): JWT token from the local utility provider
        account_number (str): Account number associated with the meters
        meter_type (str): Type of meter to get (water, electric, gas)

    Returns:
        dict | None: A dictionary of meters if successful, None otherwise.
    """
    data_vendor_url = "https://my-nwbry.sensus-analytics.com/account/details"
    params = {
        "sso_auth": jwt_token,
    }
    data = {"accountNumber": account_number, "meterTypeByValue": meter_type}
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": f"https://my-nwbry.sensus-analytics.com/main.html?sso_auth={jwt_token}",
        "Origin": "https://my-nwbry.sensus-analytics.com",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json; charset=UTF-8",
    }
    response = session.request(
        "POST", data_vendor_url, json=data, headers=headers, params=params, timeout=15
    )
    response_json = response.json()
    if response_json.get("operationSuccess") is not True:
        return None

    meters = []
    if len(response_json.get("deviceIdList")) > 0:
        for meter_id in response_json.get("deviceIdList"):
            meters.append(
                {
                    "meterId": meter_id,
                    "meterType": meter_type,
                    "meterAddress": response_json.get("devices")
                    .get(meter_id)
                    .get("address")
                    .get("line1"),
                }
            )
            if response_json.get("devices").get(meter_id).get("address").get("line2"):
                meters[-1]["meterAddress"] += (
                    f" {response_json.get('devices').get(meter_id).get('address').get('line2')}"
                )
    if len(meters) == 0:
        return None
    return meters


def main():
    """Program entry point."""
    # Add a handler for console output to the logger
    LOGGER.addHandler(StreamHandler())

    # If the user passed the -v flag, set the logging level to DEBUG
    # Use argparse to handle program arguments
    parser = argparse.ArgumentParser(
        description="Get the current meters on the AMI account from the local utility provider."
    )
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )
    args = parser.parse_args()

    if args.verbose:
        LOGGER.setLevel("DEBUG")
    else:
        LOGGER.setLevel("INFO")

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
    LOGGER.debug(
        "\x1b[1;33;20m[newberryfl.gov]\x1b[0m Creating a session with the local utility provider..."
    )
    create_utility_provider_session(session)

    # Authenticate the session with the local utility
    LOGGER.debug(
        "\x1b[1;33;20m[newberryfl.gov]\x1b[0m Authenticating with supplied username and password..."
    )
    session_authenticated = authenticate_utility_provider_session(
        session, local_utility_auth
    )
    if not session_authenticated:
        LOGGER.error("Failed to authenticate with the local utility provider.")
        return

    # Get the JWT token from the local utility provider
    LOGGER.debug(
        "\x1b[1;33;20m[newberryfl.gov]\x1b[0m Getting JWT token for AMI portal from the local utility provider..."
    )
    jwt_token = get_jwt_token_from_utility_provider(session)
    if not jwt_token:
        LOGGER.error("Failed to get the JWT token from the local utility provider.")
        return

    # Get the session cookies from the data vendor using the JWT token
    LOGGER.debug(
        "\x1b[1;35;20m[sensus-analytics.com]\x1b[0m Starting session with AMI portal using token..."
    )
    data_vendor_cookies = init_data_vendor_session(session, jwt_token)
    if not data_vendor_cookies:
        LOGGER.error("Failed to get the cookies from the data vendor.")
        return

    # Get the meters on the account
    account_meters = []
    for meter_type in ["water", "electric", "gas"]:
        LOGGER.debug(
            "\x1b[1;35;20m[sensus-analytics.com]\x1b[0m Getting all %s meters on account %s...",
            meter_type,
            local_utility_auth.get("account_number"),
        )

        meters = get_meters_by_type(
            session, jwt_token, local_utility_auth.get("account_number"), meter_type
        )
        if not meters:
            LOGGER.debug("\t- No meters of type '%s' found on the account.", meter_type)
            continue
        account_meters.extend(meters)
        LOGGER.debug(
            "\t- Found %s meter(s) of type '%s' on the account.",
            len(meters),
            meter_type,
        )
        for meter in meters:
            LOGGER.debug("\t\t- Meter ID: %s", meter["meterId"])
            LOGGER.debug("\t\t- Meter Address: %s", meter["meterAddress"])

    # Print the meter listing in json format
    output = {"meters": account_meters}
    LOGGER.debug("\nJSON Output:")
    LOGGER.info(json.dumps(output, indent=4))


if __name__ == "__main__":
    main()

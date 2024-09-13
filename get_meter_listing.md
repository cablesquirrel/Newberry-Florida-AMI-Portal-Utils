# get_meter_listing.py

## Description

Used to retrieve a list of meters on the user's account

## Usage

### Regular Mode (JSON Output)

```shell
python3 get_meter_listing.py
```

Output

```json
{
    "meters": [
        {
            "meterId": "12345678",
            "meterType": "water",
            "meterAddress": "1234 Easy St"
        },
        {
            "meterId": "87654321",
            "meterType": "electric",
            "meterAddress": "1234 Easy St"
        }
    ]
}
```

### Verbose Logging Mode (For Debugging)

```shell
python3 get_meter_listing.py -v
```

Output

```ini
[newberryfl.gov] Creating a session with the local utility provider...
[newberryfl.gov] Authenticating with supplied username and password...
[newberryfl.gov] Getting JWT token for AMI portal from the local utility provider...
[sensus-analytics.com] Starting session with AMI portal using token...
[sensus-analytics.com] Getting all water meters on account 12345...
        - Found 1 meter(s) of type 'water' on the account.
                - Meter ID: 12345678
                - Meter Address: 1234 Easy St
[sensus-analytics.com] Getting all electric meters on account 12345...
        - Found 1 meter(s) of type 'electric' on the account.
                - Meter ID: 87654321
                - Meter Address: 1234 Easy St
[sensus-analytics.com] Getting all gas meters on account 12345...
        - No meters of type 'gas' found on the account.

JSON Output:
{
    "meters": [
        {
            "meterId": "12345678",
            "meterType": "water",
            "meterAddress": "1234 Easy St"
        },
        {
            "meterId": "87654321",
            "meterType": "electric",
            "meterAddress": "1234 Easy St"
        }
    ]
}
```

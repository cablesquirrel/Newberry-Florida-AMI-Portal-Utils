# 🐍 Newberry Utility Scripts

Collection of Python scripts for retrieving utility data from Newberry, Florida city utilities.

![image](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)

## 📝 Description

Utilities contained within this repository were created to allow residents of Newberry, FL
that have been converted to smart meters (electric, water, or gas) to retrieve their utility data.

The city's 'AMI' (Advanced Metering Infrastructure) system uses a 3rd party service, Sensus-Analytics
on the backend to store and display the data collected.

No method was provided for residents to access their raw data easily, thus the need for these tools.

## ✅ Pre-requisites

- Python 3.12 check out [PyENV](Phttps://github.com/pyenv/pyenv) for managing Python versions
- Python Poetry ([https://python-poetry.org/](https://python-poetry.org/)) for managing dependencies

## 🌎 Environment Variables

This project utilizes a `.env` file to store user credentials for authenticating with the utility provider. You
must create this file in the root of the project.

`.env.example` is provided as a template for the required variables. Duplicate this file as `.env` and fill in the required values.

```shell
# Username and password used to log into utility website
UTILITY_USERNAME="12345"
UTILITY_PASSWORD="MyPassword"

# Account Number
# Usually the same as your username
# If you are unsure, your account number can be found on your latest bill
ACCOUNT_NUMBER="12345"
```

## 📋 Virtual Environment and Dependencies

This project uses Python Poetry to manage dependencies. To install the required dependencies, run the following command:

```shell
# Install python version 3.12.5
pyenv install 3.12.5

# Activate python 3.12.5 in the current shell
pyenv shell 3.12.5

# Create a virtual environment and install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

After installation, the next time the environment is needed, simply activate the shell.

```shell
poetry shell
```

## 🏃‍➡️ Running Scripts

Below is a list of the available scripts.

Visit each script's page for details on usage.

- [get_meter_listing.py](./get_meter_listing.md)

#!/usr/bin/python3

"""Etherscan API module"""

import requests

BASE_API = 'https://api.etherscan.io/api'
API_TYPE = '?module=account&action=balance'
API_ETH = BASE_API + API_TYPE + \
    '&address=:wallet:&tag=latest&apikey=:api_key:'


class EtherWallet():
    def __init__(self, api_key, wallet):
        """Init of EtherWallet class."""
        self.__api_key = api_key
        self.__wallet = wallet

    def __api_request(self, api_url):  # TODO: masterise !
        """Make Etherscan API call"""
        try:
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as errh:
            self.last_error = errh
            return None
        except requests.exceptions.ConnectionError as errc:
            self.last_error = errc
            return None
        except requests.exceptions.Timeout as errt:
            self.last_error = errt
            return None
        except requests.exceptions.RequestException as err:
            self.last_error = err
            return None

    def update(self):
        """Update Etherscan informations."""
        self.last_error = None
        cust_url = API_ETH.replace(':wallet:', self.__wallet)
        cust_url = cust_url.replace(':api_key:', self.__api_key)
        ether_json = self.__api_request(cust_url)
        if ether_json is not None:
            self.__balance = round(float(ether_json['result']) / 10e17, 5)
            return True

        if self.last_error is None:
            self.last_error = 'Can\'t retrieve json result'
        return None

    @property
    def wallet(self):
        return self.__wallet

    @property
    def balance(self):
        return self.__balance

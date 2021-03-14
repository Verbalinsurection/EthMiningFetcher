#!/usr/bin/python3

"""Etherscan API module"""

from .api_request import Api

BASE_API = 'https://api.etherscan.io/api'
API_TYPE = '?module=account&action=balance'
API_ETH = BASE_API + API_TYPE + \
    '&address=:wallet:&tag=latest&apikey=:api_key:'


class EtherWallet():
    def __init__(self, api_key, wallet):
        """Init of EtherWallet class."""
        self.__api_key = api_key
        self.__wallet = wallet

    def update(self):
        """Update Etherscan informations."""
        api = Api()
        cust_url = API_ETH.replace(':wallet:', self.__wallet)
        cust_url = cust_url.replace(':api_key:', self.__api_key)
        ether_json = api.api_request(cust_url)
        self.__last_error = api.last_error
        if ether_json is not None:
            self.__balance = round(float(ether_json['result']) / 10e17, 5)
            return True

        if self.__last_error is None:
            self.__last_error = 'Can\'t retrieve json result'
        return None

    @property
    def wallet(self):
        return self.__wallet

    @property
    def balance(self):
        return self.__balance

    @property
    def last_error(self):
        return self.__last_error

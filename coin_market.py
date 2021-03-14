#!/usr/bin/python3

"""Coin market API module"""

from datetime import datetime

from .api_request import Api

BASE_API = 'https://api.coingecko.com/api/v3'
API_COIN = BASE_API + '/coins/markets?vs_currency=:fiat:&ids=:crypto:'


class Coin():
    def __init__(self, fiat, crypto):
        """Init of Coin class."""
        self.__fiat = fiat
        self.__crypto = crypto

    def update(self):
        """Update coin market informations."""
        api = Api()
        cust_url = API_COIN.replace(':fiat:', self.__fiat)
        cust_url = cust_url.replace(':crypto:', self.__crypto)
        coin_json = api.api_request(cust_url)
        self.__last_error = api.last_error
        if coin_json is not None:
            self.price = round(coin_json[0]['current_price'], 2)
            self.pc_24h = round(coin_json[0]['price_change_24h'], 2)
            self.ath = round(coin_json[0]['ath'], 2)
            self.last_update = datetime.strptime(
                                    coin_json[0]['last_updated'],
                                    "%Y-%m-%dT%H:%M:%S.%f%z")
            self.last_update_txt = self.last_update.strftime('%Y-%m-%d %H:%M')
            return True

        if self.__last_error is None:
            self.__last_error = 'Can\'t retrieve json result'
        return False

    @property
    def fiat(self):
        return self.__fiat

    @property
    def last_error(self):
        return self.__last_error

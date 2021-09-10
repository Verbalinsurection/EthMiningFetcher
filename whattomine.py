#!/usr/bin/python3

"""Whattomine API module"""

from .api_request import Api
from .ethpay import EthPay

BASE_API = 'https://whattomine.com/coins/151.json'


class WhatToMine():
    def get_calcul(self, hrate):
        """Update WhatToMine informations."""
        api = Api()
        cc_json = api.api_request(BASE_API)
        self.__last_error = api.last_error
        if cc_json is not None:
            difficulty = cc_json['difficulty'] / 1e12
            block_time = float(cc_json['block_time'])
            block_reward = cc_json['block_reward']

            earn_hour = (hrate * 1e6 /
                         ((difficulty / block_time) * 1000 * 1e9)) * \
                        ((60 / block_time) * block_reward) * 60

            eth_pay = EthPay()
            eth_pay.eth_hour = round(earn_hour, 5)
            eth_pay.eth_day = round(earn_hour * 24, 5)
            eth_pay.eth_week = round(earn_hour * 24 * 7, 5)
            eth_pay.eth_month = round(earn_hour * 24 * 30, 5)

            return eth_pay

        if self.__last_error is None:
            self.__last_error = 'Can\'t retrieve json result'
        return None

    @property
    def last_error(self):
        return self.__last_error

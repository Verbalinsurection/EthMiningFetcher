#!/usr/bin/python3

"""Coincalculators API module"""

from .api_request import Api
from .ethpay import EthPay

BASE_API = 'https://www.coincalculators.io/api'
CC_API = BASE_API + '?name=:crypto:&hashrate=:hrate:'


class CoinCalculators():
    def __init__(self, crypto):
        """Init of CoinCalculators class."""
        self.__crypto = crypto

    def get_calcul(self, hrate):
        """Update CoinCalculators informations."""
        api = Api()
        cust_url = CC_API.replace(':crypto:', self.__crypto)
        cust_url = cust_url.replace(':hrate:', str(hrate * 1000000))
        cc_json = api.api_request(cust_url)
        self.__last_error = api.last_error
        if cc_json is not None:
            eth_pay = EthPay()
            eth_pay.eth_hour = round(cc_json['rewardsInHour'], 5)
            eth_pay.eth_day = round(cc_json['rewardsInDay'], 5)
            eth_pay.eth_week = round(cc_json['rewardsInWeek'], 5)
            eth_pay.eth_month = round(cc_json['rewardsInMonth'], 5)
            return eth_pay

        if self.__last_error is None:
            self.__last_error = 'Can\'t retrieve json result'
        return None

    @property
    def last_error(self):
        return self.__last_error

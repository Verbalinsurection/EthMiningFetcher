#!/usr/bin/python3

"""Coincalculators API module"""

import requests

from .ethpay import EthPay

BASE_API = 'https://www.coincalculators.io/api'
CC_API = BASE_API + '?name=:crypto:&hashrate=:hrate:'


class CoinCalculators():
    def __init__(self, crypto):
        """Init of CoinCalculators class."""
        self.__crypto = crypto

    def __api_request(self, api_url):
        """Make CoinCalculators API call"""
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

    def get_calcul(self, hrate):
        """Update CoinCalculators informations."""
        self.last_error = None
        cust_url = CC_API.replace(':crypto:', self.__crypto)
        cust_url = cust_url.replace(':hrate:', str(hrate * 1000000))
        cc_json = self.__api_request(cust_url)
        if cc_json is not None:
            eth_pay = EthPay()
            eth_pay.eth_hour = round(cc_json['rewardsInHour'], 5)
            eth_pay.eth_day = round(cc_json['rewardsInDay'], 5)
            eth_pay.eth_week = round(cc_json['rewardsInWeek'], 5)
            eth_pay.eth_month = round(cc_json['rewardsInMonth'], 5)
            return eth_pay

        self.last_error = 'Can\'t retrieve json result'
        return None

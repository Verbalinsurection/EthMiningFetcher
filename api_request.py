#!/usr/bin/python3

import requests


class Api():
    def __init__(self):
        self.__last_error = None

    def api_request(self, api_url):
        """Make Ethermine API call"""
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

    @property
    def last_error(self):
        return self.__last_error

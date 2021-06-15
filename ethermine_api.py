#!/usr/bin/python3

"""Ethermine API module"""

from datetime import datetime, timedelta
import pytz

from .api_request import Api
from .ethpay import EthPay

ETHM_API_BASE = 'https://api.ethermine.org'
ETHM_API_POOLSTATS = ETHM_API_BASE + '/poolStats'
ETHM_API_MINERDASH = ETHM_API_BASE + '/miner/:miner/dashboard'
ETHM_API_MINERSTAT = ETHM_API_BASE + '/miner/:miner/currentStats'
ETHM_API_MINERPAYOUT = ETHM_API_BASE + '/miner/:miner/payouts'
ETHM_API_WORKER = ETHM_API_BASE + '/miner/:miner/worker/:worker/history'

DATE_FORMAT = '%Y-%m-%d %H:%M'
MINER_TAG = ':miner'
WORKER_TAG = ':worker'


def hrate_mh(hashrate):
    return round(hashrate / 1000000, 2)


class Ethermine():
    __pool_name = 'Ethermine'

    def __init__(self, eth_wallet, history=True):
        """Init of Ethermine class."""
        self.__wallet = eth_wallet
        self.__history = history
        self.workers = []
        self.payouts = []
        self.stats_histo = []
        self.avg_hrate_1 = [0.0] * 3  # actual, 30m, 60m
        self.avg_hrate_6 = [0.0] * 3  # actual, 30m, 60m
        self.avg_hrate_24 = [0.0] * 3  # actual, 30m, 60m
        self.eth_pay_stats = EthPay()
        self.eth_pay_from_last = EthPay()
        self.__last_error = None

    def update(self):
        """Update Ethermine informations."""
        self.__last_error = None
        self.__update_pool()
        self.__update_miner_dash()
        self.__update_miner_payouts()
        self.__update_stats_coin()
        self.__update_next_payout()
        if self.__last_error is not None:
            return False
        return True

    def __update_pool(self):
        """Update Ethermine pool informations."""
        api = Api()
        pool_json = api.api_request(ETHM_API_POOLSTATS)
        self.__last_error = api.last_error
        if pool_json is None:
            self.pool_state = 'Unavailable'
            if self.__last_error is None:
                self.__last_error = \
                    '__update_pool -- Can\'t retrieve json result'
        else:
            self.pool_state = pool_json['status']

    def __update_miner_dash(self):
        """Update Ethermine miner dashboard."""
        api = Api()
        cust_url = ETHM_API_MINERDASH.replace(MINER_TAG, self.__wallet)
        dash_json = api.api_request(cust_url)
        self.__last_error = api.last_error
        if dash_json is not None:
            try:
                data_json = dash_json['data']
                self.workers.clear()
                for json_worker in data_json['workers']:
                    worker = Worker(self.__wallet, json_worker, self.__history)
                    self.workers.append(worker)
                cstat_json = data_json['currentStatistics']
                self.stat_time = datetime.utcfromtimestamp(cstat_json['time'])
                self.stat_time_txt = self.stat_time.strftime(DATE_FORMAT)
                self.reported_hrate = hrate_mh(cstat_json['reportedHashrate'])
                self.current_hrate = hrate_mh(cstat_json['currentHashrate'])
                self.valid_shares = cstat_json['validShares']
                self.invalid_shares = cstat_json['invalidShares']
                self.stale_shares = cstat_json['staleShares']
                self.active_workers = cstat_json['activeWorkers']
                self.unpaid_balance = round(cstat_json['unpaid'] / 10e17, 5)
                self.min_payout = round(
                    data_json['settings']['minPayout'] / 10e17, 5)
                if self.__history:
                    self.stats_histo.clear()
                    for json_histo in data_json['statistics']:
                        stat_histo = EthermineH(json_histo)
                        self.stats_histo.append(stat_histo)
                    self.last_histo = \
                        self.stats_histo[len(self.stats_histo) - 1 - 3]
                    self.max_index = len(self.stats_histo) - 1
                    self.calc_avg()
            except KeyError as e:
                self.__last_error = '__update_miner_dash: ' + str(e)
        else:
            if self.__last_error is None:
                self.__last_error = \
                    '__update_miner_dash -- Can\'t retrieve json result'

    def __sub_avg(self, h_range, max_index):
        all_hrate = 0
        for index in range(h_range):
            all_hrate += self.stats_histo[max_index - index].current_hrate
        return round(all_hrate / h_range, 0)

    def calc_avg(self):
        nb_entry = len(self.stats_histo)
        max_index = self.max_index

        self.avg_hrate_1[0] = self.__sub_avg(6, max_index)
        self.avg_hrate_1[1] = self.__sub_avg(6, max_index - 3)
        self.avg_hrate_1[2] = self.__sub_avg(6, max_index - 6)
        self.avg_hrate_6[0] = self.__sub_avg(36, max_index)
        self.avg_hrate_6[1] = self.__sub_avg(36, max_index - 3)
        self.avg_hrate_6[2] = self.__sub_avg(36, max_index - 6)
        self.avg_hrate_24[0] = self.__sub_avg(nb_entry, max_index)
        self.avg_hrate_24[1] = self.__sub_avg(nb_entry - 3, max_index - 3)
        self.avg_hrate_24[2] = self.__sub_avg(nb_entry - 6, max_index - 6)

    def __update_miner_payouts(self):
        api = Api()
        cust_url = ETHM_API_MINERPAYOUT.replace(MINER_TAG, self.__wallet)
        payouts_json = api.api_request(cust_url)
        self.__last_error = api.last_error
        if payouts_json is not None:
            self.payouts.clear()
            for json_payout in payouts_json['data']:
                payout = Payout(json_payout)
                self.payouts.append(payout)
        else:
            if self.__last_error is None:
                self.__last_error = \
                    '__update_miner_payouts -- Can\'t retrieve json result'
            return
        time_delta = datetime.utcnow() - self.payouts[0].paid_on
        time_delta_m = time_delta.days * 1440 + (time_delta.seconds / 60)
        gain_min = self.unpaid_balance / (time_delta_m)
        self.eth_pay_from_last.eth_hour = round(gain_min * 60, 5)
        self.eth_pay_from_last.eth_day = round(gain_min * 60 * 24, 5)
        self.eth_pay_from_last.eth_week = round(gain_min * 60 * 24 * 7, 5)
        self.eth_pay_from_last.eth_month = round(gain_min * 60 * 24 * 30, 5)
        self.gain_progress = self.unpaid_balance / self.min_payout

    def __update_stats_coin(self):
        api = Api()
        cust_url = ETHM_API_MINERSTAT.replace(MINER_TAG, self.__wallet)
        stats_json = api.api_request(cust_url)
        self.__last_error = api.last_error
        if stats_json is not None:
            coins_pmin = stats_json['data']['coinsPerMin']
            self.eth_pay_stats.eth_min = coins_pmin
            self.eth_pay_stats.eth_hour = round(coins_pmin * 60, 5)
            self.eth_pay_stats.eth_day = round(coins_pmin * 60 * 24, 5)
            self.eth_pay_stats.eth_week = round(coins_pmin * 60 * 24 * 7, 5)
            self.eth_pay_stats.eth_month = round(coins_pmin * 60 * 24 * 30, 5)
        else:
            if self.__last_error is None:
                self.__last_error = \
                    '__update_stats_coin -- Can\'t retrieve json result'

    def __update_next_payout(self):
        to_gain = self.min_payout - self.unpaid_balance
        minutes_to_tresh = to_gain / (self.eth_pay_stats.eth_hour / 60)
        next_week = self.payouts[0].paid_on.replace(tzinfo=pytz.UTC) \
            + timedelta(days=7)

        self.next_payout = \
            datetime.utcnow() + \
            timedelta(minutes=minutes_to_tresh)
        self.next_payout = self.next_payout.replace(tzinfo=pytz.UTC)

        if self.next_payout > next_week:
            self.next_payout = next_week

        time_diff_next = self.next_payout - datetime.now().astimezone()

        self.unpaid_at_next = round(
            (time_diff_next.total_seconds() *
             (self.eth_pay_stats.eth_min / 60) + self.unpaid_balance), 5)

        if self.unpaid_at_next < 0.1:
            to_gain = 0.1 - self.unpaid_balance
            minutes_to_tresh = to_gain / (self.eth_pay_stats.eth_hour / 60)
            self.next_payout = \
                datetime.utcnow() + \
                timedelta(minutes=minutes_to_tresh)
            self.next_payout = self.next_payout.replace(tzinfo=pytz.UTC)
            self.unpaid_at_next = 0.1

        self.next_payout_txt = \
            self.next_payout.strftime(DATE_FORMAT)

    @property
    def wallet(self):
        return self.__wallet

    @property
    def pool_name(self):
        return self.__pool_name

    @property
    def last_error(self):
        return self.__last_error


class EthermineH():
    def __init__(self, json_data):
        self.stat_time = datetime.fromtimestamp(
            json_data['time']).astimezone()
        self.stat_time_txt = self.stat_time.strftime(DATE_FORMAT)
        self.reported_hrate = hrate_mh(json_data['reportedHashrate'])
        self.current_hrate = hrate_mh(json_data['currentHashrate'])
        self.valid_shares = json_data['validShares']
        self.invalid_shares = json_data['invalidShares']
        self.stale_shares = json_data['staleShares']


class Worker(Ethermine):
    def __init__(self, wallet, json_data, history):
        self.stats_histo = []
        self.avg_hrate_1 = [0.0] * 3  # actual, 30m, 60m
        self.avg_hrate_6 = [0.0] * 3  # actual, 30m, 60m
        self.avg_hrate_24 = [0.0] * 3  # actual, 30m, 60m
        self.__wallet = wallet
        self.name = json_data['worker']
        self.last_seen = json_data['lastSeen']
        self.reported_hrate = hrate_mh(json_data['reportedHashrate'])
        self.current_hrate = hrate_mh(json_data['currentHashrate'])
        self.valid_shares = json_data['validShares']
        self.invalid_shares = json_data['invalidShares']
        self.stale_shares = json_data['staleShares']
        if history:
            self.__process_histo()

    def __process_histo(self):
        api = Api()
        cust_url = ETHM_API_WORKER.replace(MINER_TAG, self.__wallet)
        cust_url = cust_url.replace(WORKER_TAG, self.name)
        dash_json = api.api_request(cust_url)
        self.__last_error = api.last_error
        if dash_json is not None:
            try:
                data_json = dash_json['data']
                self.stats_histo.clear()
                for json_histo in data_json:
                    stat_histo = EthermineH(json_histo)
                    self.stats_histo.append(stat_histo)
                self.last_histo = \
                    self.stats_histo[len(self.stats_histo) - 1 - 3]
                self.max_index = len(self.stats_histo) - 1
                self.calc_avg()
            except KeyError as e:
                print(e)
        else:
            if self.__last_error is None:
                self.__last_error = \
                    '__process_histo -- Can\'t retrieve json result'

    @property
    def last_error(self):
        return self.__last_error


class Payout():
    def __init__(self, json_data):
        self.paid_on = datetime.utcfromtimestamp(
            json_data['paidOn'])
        self.paid_on_txt = self.paid_on.strftime(DATE_FORMAT)
        self.amount = round(json_data['amount'] / 10e17, 5)

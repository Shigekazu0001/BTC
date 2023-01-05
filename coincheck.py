import hmac
import hashlib
import json
import time
import requests


class Coincheck(object):
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key
        self.url = 'https://coincheck.com'

    def _request(self, endpoint, params=None, method='GET'):
        time.sleep(1)
        nonce = str(int(time.time()))
        body = json.dumps(params) if params else ''

        message = nonce + endpoint + body
        signature = hmac.new(self.secret_key.encode(),
                             message.encode(),
                             hashlib.sha256).hexdigest()

        headers = {
            'ACCESS-KEY': self.access_key,
            'ACCESS-NONCE': nonce,
            'ACCESS-SIGNATURE': signature,
            'Content-Type': 'application/json'
        }

        if method == 'GET':
            r = requests.get(endpoint, headers=headers, params=params)
        else:
            r = requests.post(endpoint, headers=headers, data=body)

        return r.json()

    def ticker(self):
        endpoint = self.url + '/api/ticker'
        return self._request(endpoint=endpoint)

    @property
    def last(self):
        return self.ticker()['last']

    def trades(self, params):
        endpoint = self.url + '/api/trades'
        return self._request(endpoint=endpoint, params=params)

    def order_books(self, params={
        'limit': 1
    }):
        
        endpoint = self.url + '/api/order_books'
        return self._request(endpoint=endpoint, params=params)

    def balance(self):
        endpoint = self.url + '/api/accounts/balance'
        return self._request(endpoint=endpoint)

    @property
    def position(self):
        balance = self.balance()
        return {k: v for k, v in balance.items()
                if isinstance(v, str) and float(v)}

    def order(self, params):
        
        endpoint = self.url + '/api/exchange/orders'
        return self._request(endpoint=endpoint, params=params, method='POST')

    def transaction(self):
        endpoint = self.url + '/api/exchange/orders/transactions'
        return self._request(endpoint=endpoint)

    @property
    def ask_rate(self):
        transaction = self.transaction()
        
        ask_transaction = [d for d in transaction['transactions']
                           if d['side'] == 'buy']
        ask_stransaction = [d for d in transaction['transactions']
                           if d['side'] == 'sell']
        last_list=[float(ask_transaction[0]['rate']),float(ask_stransaction[0]['rate'])]
        return last_list



    def rate(self, params):
        endpoint = self.url + '/api/exchange/orders/rate'
        return self._request(endpoint=endpoint, params=params)

    def next_ticker(self, params={'pair': 'btc_jpy'}):
        endpoint = self.url + '/api/trades'
        return self._request(endpoint=endpoint, params=params)

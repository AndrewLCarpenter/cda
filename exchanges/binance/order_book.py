import pytz
from datetime import datetime as dt
import json
import pprint

class OrderBook:
    """
    Stores the state of the orderbook. Use initialize() to get base set of
    orders using REST endpoint then update() to pass subsequent orders that
    are pulled from the websocket.
    """

    tz = pytz.timezone('US/Eastern')

    def __init__(self):
        self.bids = {}
        self.asks = {}
        self.last_update_id = 0
        self.timestamp = 0

    def initialize(self, depth_dict):
        """
        Initialize the orderbook instance by pulling from RESTful depth endpoint

        Parameters
        ----------
        depth_dict : dict
            json.loads(response.content) for requests.get() call

        References
        ----------
        https://www.binance.com/restapipub.html#user-content-market-data-endpoints

        """
        # TODO: sync v1/depth id to ws/@depth id before streaming
        # TODO: logging

        if not isinstance(depth_dict, dict):
            raise Exception("Invalid book. Pass a dictionary")
        if 'lastUpdateId' in depth_dict:
            self.last_update_id = depth_dict['lastUpdateId']
            self.bids = {k: v for k, v, _ in depth_dict['bids'] if float(v) != 0.0}
            self.asks = {k: v for k, v, _ in depth_dict['asks'] if float(v) != 0.0}
        else:
            raise Exception('Invalid depth dictionary')

    def update(self, update_dict):
        """
        Add new dictionary of orderbook values to current orderbook instance.

        Parameters
        ----------
        update_dict : dict
            dictionary containing new order book values

        References
        ----------
        https://www.binance.com/restapipub.html#depth-wss-endpoint

        """
        if not isinstance(update_dict, dict):
            raise Exception("Invalid book. Pass a dictionary")

        if update_dict['e'] != 'depthUpdate':
            raise Exception('Invalid event type -- requires depthUpdate')

        if update_dict['u'] >= self.last_update_id:
            self.last_update_id = update_dict['u']
            self.timestamp = update_dict['E']
            try:
                self._replace_bids(update_dict['b'])
                self._replace_asks(update_dict['a'])
            except Exception as e:
                print('REPLACEMENT FAILURE: %s' % (e))
                # with open('tmpfile.txt', 'w') as w:
                #     json.dump(self.bids, w, indent=2)
                #     w.write('\n')
                #     w.write('API UPDATE:')
                #     json.dump(update_dict, w, indent=2)
                #     exit(1)

    def _replace_bids(self, new_vals):
        """
        Find and replace values in orderbook. We dont check for 0.000 first
        because the del statement will throw an error if that value doesnt exist.
        The performance cost isn't very high doing it this way, so keep for now.
        """
        for k, v, _ in new_vals:
            self.bids[k] = v
            if float(v) == 0.0:
                del self.bids[k]

    def _replace_asks(self, new_vals):
        """See  _replace_bids"""
        for k, v, _ in new_vals:
            self.asks[k] = v
            if float(v) == 0.0:
                del self.asks[k]

    def dump(self, style=None):
        """
        Return dictionary ready to be written to database
        
        Parameters
        ----------
        style : str
            output type -- (arctic or general dictionary)

        Returns
        -------
        d : dict
        """
        if style == 'arctic':
            d = {}
            d['index'] = dt.fromtimestamp(self.timestamp/1000.0,
                                                 tz=self.tz)
            d['depth_id'] = self.last_update_id
            sort_bids = sorted(self.bids, reverse=True)
            sort_asks = sorted(self.asks)
            for n, k in enumerate(sort_bids):
                d[f'bid{n+1}'] = k
                d[f'bid{n+1}_ammt'] = self.bids[k]
            for n, k in enumerate(sort_asks):
                d[f'ask{n+1}'] = k
                d[f'ask{n+1}_ammt'] = self.asks[k]
            # print(d['bid1'], d['bid1_ammt'])
            return [d]
        else:
            d = {'id': self.last_update_id,
                 'timestamp': self.timestamp,
                 'bids': self.bids,
                 'asks': self.asks}
            return d




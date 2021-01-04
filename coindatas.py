from bithumb_api import *
import pandas as pd
import numpy as np
import math
import time

class CoinDatas :
    def __init__(self,conkey,seckey):
        self.api = PrivateApi(conkey, seckey)

    @staticmethod
    def convert_unit(unit) :
        try :
            unit = math.floor(unit*10000) / 10000
            return unit
        except :
            return 0

    def get_orderable_buying_unit(self, order_currency, price) :
        try :
            """
            tickers = self.get_tickers(order_currency)
            current_price = float(tickers['closing_price'])
            """
            balance = self.get_balance(order_currency)
            available_krw = balance[5]
            unit = (available_krw / price)*0.98*0.9975 #fee(0.25%) 
            unit = self.convert_unit(unit)
            return unit
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None

    def get_orderable_selling_unit(self, order_currency) :
        try :
            balance = self.get_balance(order_currency)
            available_currency = balance[4]
            unit = math.floor(available_currency*10000)/10000
            return unit
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None

    def get_buying_price(self, order_currency) :
        try :
            buying_price = self.get_orderbook(order_currency)['bids'][0]['price']
            return buying_price
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None

    def get_selling_price(self, order_currency) :
        try :
            selling_price = self.get_orderbook(order_currency)['asks'][0]['price']
            return selling_price
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None
        
    @staticmethod
    def get_tickers(order_currency) :
        try :
            data = PublicApi.ticker(order_currency)
            data = data['data']
            return data
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None

    @staticmethod
    def get_current_price(order_currency) :
        try :
            data = PublicApi.ticker(order_currency)
            return float(data['data']['closing_price'])
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None

    @staticmethod
    def get_orderbook(order_currency, payment_currency="KRW", limit=5) :
        try :
            limit = min(limit, 30)
            data = PublicApi.orderbook(order_currency, payment_currency, limit)
            data = data['data']
            for idx in range(len(data['bids'])) :
                data['bids'][idx]['quantity'] = float(data['bids'][idx]['quantity'])
                data['bids'][idx]['price'] = float(data['bids'][idx]['price'])
                data['asks'][idx]['quantity'] = float(data['asks'][idx]['quantity'])
                data['asks'][idx]['price'] = float(data['asks'][idx]['price'])
            return data
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None

    def get_candlestick(self, order_currency,payment_currency="KRW",
                        chart_instervals="10m") :
        try :
            data = PublicApi.candlestick(order_currency,payment_currency,chart_instervals)
            current_price = self.get_current_price(order_currency)
            if data['status'] == '0000' and current_price is not None:
                data = data['data']
                #current_data = [time.time(), "0.", current_price, "0.","0.","0."]
                #data.append(current_data)
                df = pd.DataFrame(data, columns = ['time','open','close','high','low','volume'])
                df = df.set_index('time')
                df.index = pd.to_datetime(df.index, unit = 'ms', utc = True)
                df.index = df.index.tz_convert('Asia/Seoul')
                df.index = df.index.tz_localize(None)
                df = df.astype(float)
                df['close'][-1] = current_price
                df['ma5'] = df['close'].rolling(window = 5).mean()
                df['ma20'] = df['close'].rolling(window = 20).mean()
                df['ma30'] = df['close'].rolling(window = 30).mean()
                df['ma60'] = df['close'].rolling(window = 60).mean()

                return df
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None

    def get_balance(self, currency) :
        try :
            data = self.api.balance(currency = currency)
            currency = currency.lower()
            return (float(data['data']['total_' + currency]),
                    float(data['data']['total_krw']),
                    float(data['data']['in_use_' + currency]),
                    float(data['data']['in_use_krw']),
                    float(data['data']['available_' + currency]),
                    float(data['data']['available_krw']),
                    float(data['data']['xcoin_last_' + currency]))
                    
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None

    def order_place_buy(self, order_currency, price, unit,
                        payment_currency = "KRW") :
        try :
            data = self.api.place(type = "bid", price = price, units= unit,
                                  order_currency = order_currency,
                                  payment_currency= payment_currency)
            print(data)
            return "bid", order_currency, data['order_id'], payment_currency, price
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None

    def order_market_buy(self, order_currency, unit, payment_currency = "KRW") :
        try:
            price = self.get_orderbook(order_currency)['asks'][2]['price']
            if price > 1000.0 :
                price = int(price)
            data = self.api.place(type = "bid", price = price, units= unit,
                                  order_currency = order_currency,
                                  payment_currency= payment_currency)
            print(data)
            return "bid", order_currency, data['order_id'], payment_currency, price
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None

    def order_place_sell(self, order_currency, price, unit,
                         payment_currency="KRW") :
        try :
            data = self.api.place(type = "ask", price = price, units = unit,
                                  order_currency = order_currency,
                                  payment_currency = payment_currency)
            return "ask", order_currency, data['order_id'], payment_currency, price
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None

    def order_market_sell(self, order_currency, unit, payment_currency = "KRW") :
        try :
            price = self.get_orderbook(order_currency)['bids'][2]['price']
            if price > 1000.0 :
                price = int(price)
            data = self.api.place(type = "ask", price = price, units = unit,
                                  order_currency = order_currency,
                                  payment_currency = payment_currency)
            return "ask", order_currency, data['order_id'], payment_currency, price
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None

    def get_outstanding_order(self, order_desc) :
        try :
            data = self.api.orders(type = order_desc[0], order_currency = order_desc[1],
                                   order_id = order_desc[2], payment_currency = order_desc[3])
            if data['status'] == '5600':
                return None
            return data['data'][0]['units_remaining']
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None

    def get_completed_order(self, order_desc) :
        try :
            data = self.api.order_detail(order_currency = order_desc[1],
                                         order_id = order_desc[2],payment_currency = order_desc[3])
            if data['status'] == '5600':
                return None
            return data['data'][0]
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None

    def cancel_order(self, order_desc):
        try :
            data = self.api.cancel(type = order_desc[0], order_currency = order_desc[1],
                                   order_id = order_desc[2], payment_currency = order_desc[3])
            return data['status'] == '0000'
        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None


import sys
from coindatas import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
import time
import openpyxl

api_key = "";
api_secret = "";

coins = ["BTC","ETH","LTC","BCH","BSV","ADA","EOS","TRX","XLM","LINK"]#MAJOR COINS
coin_data = CoinDatas(api_key,api_secret)
ordered = {}
installment = False

class Worker(QThread) :
    write_wb = None
    try :
        write_wb = openpyxl.load_workbook('golden-cross.xlsx')
    except :
        write_wb = openpyxl.Workbook()
    write_ws = write_wb.active
    if write_ws['A1'] is not 'time' :
        write_ws['A1'] = 'time'
        write_ws['B1'] = 'buy'
        write_ws['C1'] = 'sell'
        
    def run(self) :
        for coin in coins :
            ordered[coin] = [0,False]
            
        while True :
            data = {}

            for coin in coins :
                data[coin] = self.auto_trading(coin)

            print(data, end = '\n\n')
            self.write_wb.save('golden-cross.xlsx')
            time.sleep(60)

    def auto_trading(self, coin) :
        try :
            candle_day = coin_data.get_candlestick(coin,chart_instervals = "24h")

            if candle_day['close'][-1] < candle_day['ma20'][-1] :
                return None, None, None, None
            
            candle = coin_data.get_candlestick(coin)
            
            current_price = candle['close'][-1]
            if current_price > 1000.0 :
                current_price = int(current_price)

            balance = coin_data.get_balance(coin)

            state = self.check_golden_cross(candle)
            trade_time = time.strftime('%y-%m-%d %H:%M:%S',time.localtime(time.time()))

            if balance[0] >= 0.0001 :
                if state is 'dead_cross' :
                    unit = coin_data.get_orderable_selling_unit(coin)
                    if unit > 0.0000 :
                        self._sell(coin,unit)
                        self.write_ws.append([trade_time,"",current_price])
                        ordered[coin] = [0,False]

                elif not ordered[coin][1] and ordered[coin][0] > 0:
                    if ordered[coin][0]*1.015 < current_price :
                        unit = coin_data.convert_unit(coin_data.get_orderable_selling_unit(coin)/2)
                        self._sell(coin,unit)
                        self.write_ws.append([trade_time,"",current_price])
                        ordered[coin][1] = True
                
            
            else :
                if state is 'golden_cross' and balance[0] <0.0001:
                    unit = coin_data.get_orderable_buying_unit(coin,current_price)

                    if unit > 0.0001 and unit * current_price > 1000.0:
                        self._buy(coin,unit)
                        self.write_ws.append([trade_time,current_price,""])
                        ordered[coin] = [current_price, False]

            return trade_time, state, current_price

        except Exception as e:
            print(f"{type(e).__name__}:{e}")
            return None, None, None, None

    @staticmethod
    def _buy(coin,unit) :
        ordered = coin_data.order_market_buy(coin,unit)
        print(ordered)

    @staticmethod
    def _sell(coin, unit) :
        ordered = coin_data.order_market_sell(coin,unit)
        print(ordered)

    @staticmethod
    def check_golden_cross(candle) :
        pre_ma5 = candle['ma5'][-2]
        pre_ma20 = candle['ma20'][-2]
        price = candle['close'][-1]
        ma5 = candle['ma5'][-1]
        ma20 = candle['ma20'][-1]



        if ma5 >= ma20 and price >= ma5:
            if pre_ma5 <= pre_ma20 and price <= ma5 * 1.01:
                return 'golden_cross'

            else :
                return 'holding'
        elif ma5 < ma20 * 1.001 :
            return 'dead_cross'
        else :
            return 'nothing' 
        

class MyWindow(QMainWindow) :
    def __init__(self) :
        super().__init__()

        self.worker = Worker()
        self.worker.start()

if __name__ == "__main__" :
    coin_data = CoinDatas(api_key, api_secret)

    app = QApplication(sys.argv)
    mywindow = MyWindow()
    mywindow.show()
    app.exec_()

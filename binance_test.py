import pandas as pd
from datetime import datetime, timedelta
from binance.client import Client
import requests
import ccxt
from pprint import pprint
import requests
#####################################################################################
# 바이낸스 Funcion 
# API 키 수정 필요
api_key = ''
api_secret = '' 
#####################################################################################

# Binance Server Time
def get_server_time():
    url = 'https://fapi.binance.com/fapi/v1/time'
    response = requests.get(url)
    data = response.json()
    server_time = int(data['serverTime'])
    server_time = datetime.fromtimestamp(server_time / 1000)

    return server_time


def get_cur_nex_wait_time():
    server_time = get_server_time()
    current_minute = server_time.replace(second=0, microsecond=0)
    next_minute =  current_minute + timedelta(minutes=1)
    wait_time = (next_minute - server_time).total_seconds()
    
    return current_minute, next_minute, wait_time


# Get Binance DataFrame
def get_data(start_date, end_date, symbol):
    client = Client(api_key=api_key, api_secret=api_secret)
    data = client.futures_historical_klines(
        symbol=symbol,
        interval='1m',
        start_str=start_date,
        end_str=end_date
    )
    COLUMNS = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore']
    df = pd.DataFrame(data, columns=COLUMNS)
    df['open_time'] = df.apply(lambda x: datetime.fromtimestamp(x['open_time'] // 1000), axis=1)
    df = df.drop(columns=['close_time', 'ignore'])
    df['symbol'] = symbol
    df.loc[:, 'open':'tb_quote_av'] = df.loc[:, 'open':'tb_quote_av'].astype(float)
    df['trades'] = df['trades'].astype(int)
    
    return df

def set_binance():
    # 바이낸스 선물 계좌 객체 생성
    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future'
        }
    })
    
    return exchange


def get_price(exchange, symbol):
    parts = symbol.split('USDT')
    formatted_symbol = parts[0] + '/USDT'
    ticker = exchange.fetch_ticker(formatted_symbol)
    
    return ticker['last']

def get_price2(symbol):
    url = f'https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}'
    response = requests.get(url)
    data = response.json()
    return float(data['price'])


def set_leverage(exchange):
    symbol1 = 'BTC/USDT:USDT'
    symbol2 = 'ETH/USDT:USDT'
    symbol3 = 'XRP/USDT:USDT'
    leverage = 10  
    params = {'marginMode': 'isolated'}  
    
    try:
        response1 = exchange.setLeverage(leverage, symbol1, params)
        response2 = exchange.setLeverage(leverage, symbol2, params)
        response3 = exchange.setLeverage(leverage, symbol3, params)
        print('Leverage set successfully:', response1, response2, response3)
    except Exception as e:
        print('Error setting leverage:', e)
        
        
def btc_order(amount, price, side, exchange):
    orders = [None] * 2
    symbol = "BTC/USDT"
    type = "LIMIT"          # LIMIT: 지정가 주문 / MARKET: 시장가 주문          
    amount = amount         # 코인 수량          
    price = price           # 매수 가격
    price_sl = 5000         # 손절 가격
    side = side             # buy or sell
    if (side == 'buy'):
        stop_loss = 'sell'
    
    # 롱(공매수) 포지션 주문
    orders[0] = exchange.create_order(
        symbol=symbol, 
        type=type,  
        side=side, 
        amount=amount, 
        price=price, 
        params={
            'positionSide': 'LONG'
        }
    )

    # Stop Loss 주문
    orders[1] = exchange.create_order(
        symbol=symbol,
        type="STOP_MARKET",
        side=stop_loss,
        amount=amount,
        params={
            'positionSide': 'LONG',
            'stopPrice': price_sl
        }
    )

    for order in orders:
        pprint(order)

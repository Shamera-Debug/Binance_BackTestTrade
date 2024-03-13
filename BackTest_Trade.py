import asyncio
import pandas as pd
from datetime import timedelta
import numpy as np
import joblib
import time
from tensorflow.keras.models import load_model
import warnings
warnings.filterwarnings("ignore")
#####################################################################################
# Import Relational File
import binance_test
import preprocess_
import trading_logic_test
#####################################################################################
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']
REG_MODEL_PATH = '/home/zero/test1/FinalProject/model/reg_model'
CLS_MODEL_PATH = '/home/zero/test1/FinalProject/model/cls_model'
SCALER_TARGET_PATH = '/home/zero/test1/FinalProject/scaler'
SEQUENCE_LENGTH = 20
ASSET = 1000
PROFIT = 0
positions = {'BTCUSDT': None, 'ETHUSDT': None, 'XRPUSDT': None}
positions_amount = {'BTCUSDT': 0, 'ETHUSDT': 0, 'XRPUSDT': 0}
hist_price = {'BTCUSDT': None, 'ETHUSDT': None, 'XRPUSDT': None}
real_price = {'BTCUSDT': None, 'ETHUSDT': None, 'XRPUSDT': None}
positions_count = {'BTCUSDT': 0, 'ETHUSDT': 0, 'XRPUSDT': 0}
#####################################################################################
def reg_diff(reg_predictions_dict):
    # BTC 변동률 계산
    btc_diff = ((reg_predictions_dict['BTCUSDT'][5] - reg_predictions_dict['BTCUSDT'][0]) / reg_predictions_dict['BTCUSDT'][0]) * 100
    
    # ETH 변동률 계산
    eth_diff = ((reg_predictions_dict['ETHUSDT'][5] - reg_predictions_dict['ETHUSDT'][0]) / reg_predictions_dict['ETHUSDT'][0]) * 100
    
    # XRP 변동률 계산
    xrp_diff = ((reg_predictions_dict['XRPUSDT'][5] - reg_predictions_dict['XRPUSDT'][0]) / reg_predictions_dict['XRPUSDT'][0]) * 100
        
    return btc_diff, eth_diff, xrp_diff


def cls_value(cls_predictions_dict):
    if cls_predictions_dict['BTCUSDT'][0] > 0.52:
        cls_btc = 1
    elif cls_predictions_dict['BTCUSDT'][0] < 0.48:
        cls_btc = 0
    else:
        cls_btc = 0.5
    
    if cls_predictions_dict['ETHUSDT'][0] > 0.52:
        cls_eth = 1
    elif cls_predictions_dict['ETHUSDT'][0] < 0.48:
        cls_eth = 0
    else:
        cls_eth = 0.5

    if cls_predictions_dict['XRPUSDT'][0] > 0.52:
        cls_xrp = 1
    elif cls_predictions_dict['XRPUSDT'][0] < 0.48:
        cls_xrp = 0
    else:
        cls_xrp = 0.5  
    
    return cls_btc, cls_eth, cls_xrp
    



async def main_process(): 
    global ASSET, PROFIT
    global positions, positions_amount, hist_price, real_price, positions_count
    
    # 모델 로드
    reg_model = load_model(f'{REG_MODEL_PATH}')
    cls_model = load_model(f'{CLS_MODEL_PATH}')
    
    # 바이낸스 API 설정
    exchange = binance_test.set_binance()
    
    # 레버리지 설정
    binance_test.set_leverage(exchange)
    
    # 바이낸스 시간
    current_minute, next_minute, wait_time = binance_test.get_cur_nex_wait_time()
    
    if(wait_time < 15):
        print(f'다음 {wait_time}초 기다리는중...')
        time.sleep(wait_time)
        current_minute, next_minute, wait_time = binance_test.get_cur_nex_wait_time()
        
    # 과거 t분 시간 저장
    t = 45
    hist_time_60 = current_minute - timedelta(minutes=t)
    temp_end = current_minute - timedelta(minutes=1)
    start_str = str(int(hist_time_60.timestamp() * 1000))
    end_str = str(int(temp_end.timestamp() * 1000))
    
    
    data_frames = {}
    for symbol in SYMBOLS:
        df = binance_test.get_data(start_str, end_str, symbol)
        data_frames[symbol] = df
    print('과거 데이터 저장완료')
    
    count = 0
    while count < 240:
        current_minute, next_minute, wait_time = binance_test.get_cur_nex_wait_time()
         
        print(f'다음 {wait_time}초 기다리는중...')
        time.sleep(wait_time)    
        
        start_str = str(int(current_minute.timestamp() * 1000))
        end_str = str(int(next_minute.timestamp() * 1000)) 
        
        reg_X_final = []
        reg_X_final_symbol = []
        cls_X_final = []
        cls_X_final_symbol = []        
        
        for symbol in SYMBOLS:
            df_real = binance_test.get_data(start_str, end_str, symbol)
            data_frames[symbol] = pd.concat([data_frames[symbol], df_real], ignore_index=True)
            data_frames[symbol] = data_frames[symbol].drop(df.index[0])
            # 전처리
            reg_X, reg_X_symbol = preprocess_.reg_preprocess(data_frames[symbol], symbol)
            reg_X_final.extend(reg_X)
            reg_X_final_symbol.extend(reg_X_symbol)
            cls_X, cls_X_symbol = preprocess_.cls_preprocess(data_frames[symbol], symbol)
            cls_X_final.extend(cls_X)
            cls_X_final_symbol.extend(cls_X_symbol)
            
            
        reg_X_final = np.array(reg_X_final)
        reg_X_final_symbol = np.array(reg_X_final_symbol)
        cls_X_final = np.array(cls_X_final)
        cls_X_final_symbol = np.array(cls_X_final_symbol)        
        

        # 모델 예측
        reg_predictions = reg_model.predict([reg_X_final, reg_X_final_symbol])
        cls_predictions = cls_model.predict([cls_X_final, cls_X_final_symbol])
        reg_predictions_dict = {}
        cls_predictions_dict = {}

        for symbol in SYMBOLS:
            reg_test_indices = np.where(reg_X_final_symbol[:, SYMBOLS.index(symbol)] == 1)[0]
            cls_test_indices = np.where(cls_X_final_symbol[:, SYMBOLS.index(symbol)] == 1)[0]
            
            scaler_load_path = f'{SCALER_TARGET_PATH}/scaler_target_{symbol}.save'
            scaler_target = joblib.load(scaler_load_path)
            # 단일 예측값을 추출하여 저장
            reg_prediction = scaler_target.inverse_transform(reg_predictions[reg_test_indices].reshape(-1, 1)).flatten()
            reg_predictions_dict[symbol] = reg_prediction
            
            cls_predictions_dict[symbol] = cls_predictions[cls_test_indices]
        

        print(reg_predictions_dict)
        print(cls_predictions_dict)
        
        btc_diff, eth_diff, xrp_diff = reg_diff(reg_predictions_dict)
        cls_btc, cls_eth, cls_xrp = cls_value(cls_predictions_dict)  
        
        print(btc_diff, eth_diff, xrp_diff)  
        print(cls_btc, cls_eth, cls_xrp)
        print(f'시간 : {next_minute}')
                
        for symbol, diff, cls_pred in [('BTCUSDT', btc_diff, cls_btc), ('ETHUSDT', eth_diff, cls_eth), ('XRPUSDT', xrp_diff, cls_xrp)]:
            if positions[symbol] is None:  # 현재 포지션이 없는 경우
                hist_price[symbol] = binance_test.get_price2(symbol)
                positions[symbol], positions_amount[symbol], ASSET = trading_logic_test.update_position(symbol, diff, cls_pred, ASSET, hist_price[symbol])
            else:  
                real_price[symbol] = binance_test.get_price2(symbol)  # 현재 가격 가져오기
                positions[symbol], positions_amount[symbol], positions_count[symbol], ASSET, PROFIT = trading_logic_test.SL_TP(
                    symbol
                    , positions_amount[symbol]
                    , hist_price[symbol]
                    , real_price[symbol]
                    , positions[symbol]
                    , positions_count[symbol]
                    , ASSET
                    , PROFIT
                    , diff
                    , cls_pred
                    )
            
            
        print(f'현재 자산 : {ASSET}, 현재 PNL : {PROFIT}')
        count = count + 1
        
    for symbol, diff, cls_pred in [('BTCUSDT', btc_diff, cls_btc), ('ETHUSDT', eth_diff, cls_eth), ('XRPUSDT', xrp_diff, cls_xrp)]:
        # 강제 포지션 모두 종료
        positions_count[symbol] = 5
        real_price[symbol] = binance_test.get_price2(symbol)  # 현재 가격 가져오기
        positions[symbol], positions_amount[symbol], positions_count[symbol], ASSET, PROFIT = trading_logic_test.SL_TP(
            symbol
            , positions_amount[symbol]
            , hist_price[symbol]
            , real_price[symbol]
            , positions[symbol]
            , positions_count[symbol]
            , ASSET
            )
    
    profit = (ASSET-1000)/1000 * 100
    print(f'종료. 최종 자산 : {ASSET}, 최종 수익률 : {profit}%')
        
           
async def main():
    await main_process()

if __name__ == "__main__":
    asyncio.run(main())
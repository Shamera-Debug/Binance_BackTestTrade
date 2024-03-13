import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
#####################################################################################
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']
SEQ_LENGTH = 20
REG_SCALER_PATH = '/home/zero/test1/FinalProject/scaler'
CLS_SCALER_PATH = '/home/zero/test1/FinalProject/scaler'
#####################################################################################
# 이동 평균 (Moving Average, MA)
def calculate_sma(df, window):
    return df.rolling(window=window).mean()


# 볼린저 밴드 (Bollinger Bands)
def calculate_bollinger_bands(df, window):
    sma = df.rolling(window=window).mean()
    std = df.rolling(window=window).std()
    bollinger_up = sma + (std * 2)  # 상단 밴드
    bollinger_down = sma - (std * 2)  # 하단 밴드
    
    return bollinger_up, bollinger_down


# 시퀀스 생성
def create_sequences(data, seq_length):
    X, X_symbol = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length, :-3])  # 마지막 3개 컬럼 제외
        X_symbol.append(data[i+seq_length-1, -3:])  # 마지막 시퀀스의 심볼 정보만 추출
        
    return np.array(X), np.array(X_symbol)


# 각 `symbol` 그룹에 대해 차분을 수행하는 함수 정의
def diff_group(group, columns_to_diff):
    # 선택된 컬럼에 대해 차분 수행
    group_diff = group[columns_to_diff].diff()
    
    # 'symbol', 'target', 'open_time' 컬럼을 차분된 데이터프레임에 다시 추가
    group_diff['symbol'] = group['symbol'].values
    group_diff['open_time'] = group['open_time'].values
    return group_diff


def reg_preprocess(temp_df, symbol):
    df = temp_df.copy()

    df = df[df['volume'] != 0]
    df['open_time'] = pd.to_datetime(df['open_time'])
    df.sort_values(by='open_time', inplace=True)
    
    # SMA 및 볼린저 밴드 계산
    df['sma_20'] = calculate_sma(df['close'], 20)
    bollinger_up, bollinger_down = calculate_bollinger_bands(df['close'], 20)
    df['bollinger_up'] = bollinger_up
    df['bollinger_down'] = bollinger_down

    df.dropna(inplace=True)
    df.drop(columns=['open_time', 'quote_av', 'tb_base_av', 'tb_quote_av', 'trades'], inplace=True)
    
    # 원핫 인코딩 적용
    for s in SYMBOLS:
        df[f'symbol_{s}'] = df['symbol'].apply(lambda x: 1 if x == s else 0)
        
    
    # 필요한 컬럼 선택
    selected_columns = ['open', 'high', 'low', 'close', 'volume', 'sma_20', 'bollinger_up', 'bollinger_down',
                        'symbol_BTCUSDT', 'symbol_ETHUSDT', 'symbol_XRPUSDT']
    df = df[selected_columns]

    # 스케일러 로드 및 적용
    scaler_load_path = f'{REG_SCALER_PATH}/scaler_data_{symbol}.save'
    scaler_data = joblib.load(scaler_load_path)

    # 스케일링할 컬럼 선택
    scale_cols = ['open', 'high', 'low', 'close', 'volume', 'sma_20', 'bollinger_up', 'bollinger_down']

    # 스케일링 적용
    df[scale_cols] = scaler_data.transform(df[scale_cols])
    
    
    X, X_symbol = create_sequences(df.values, SEQ_LENGTH)
    
    
    return X, X_symbol


def cls_preprocess(temp_df, symbol):
    df = temp_df.copy()
    df = df.iloc[4:]
    df = df[df['volume'] != 0]
    df['open_time'] = pd.to_datetime(df['open_time'])
    df.sort_values(by='open_time', inplace=True)
    
    # SMA 및 볼린저 밴드 계산
    df['sma_20'] = calculate_sma(df['close'], 20)
    bollinger_up, bollinger_down = calculate_bollinger_bands(df['close'], 20)
    df['bollinger_up'] = bollinger_up
    df['bollinger_down'] = bollinger_down
    
    # 차분을 수행할 컬럼 선택 ('open_time', 'symbol', 'target' 제외)
    columns_to_diff = df.columns.difference(['open_time', 'symbol'])
    df = diff_group(df, columns_to_diff)
    df.dropna(inplace=True)
    df.drop(columns=['open_time', 'quote_av', 'tb_base_av', 'tb_quote_av', 'trades','open', 'high', 'low'], inplace=True)
     
    # 원핫 인코딩 적용
    for s in SYMBOLS:
        df[f'symbol_{s}'] = 1 if s == symbol else 0
        
    
    # 필요한 컬럼 선택
    selected_columns = ['close', 'volume',  'sma_20', 'bollinger_up', 'bollinger_down',
                        'symbol_BTCUSDT', 'symbol_ETHUSDT', 'symbol_XRPUSDT']
    df = df[selected_columns]

    # 스케일러 로드 및 적용
    scaler_load_path = f'{CLS_SCALER_PATH}/cls_scaler_{symbol}.save'
    scaler_data = joblib.load(scaler_load_path)

    # 스케일링할 컬럼 선택
    scale_cols = ['close', 'volume', 'sma_20', 'bollinger_up', 'bollinger_down']

    # 스케일링 적용
    df[scale_cols] = scaler_data.transform(df[scale_cols])
    
    
    X, X_symbol = create_sequences(df.values, SEQ_LENGTH)
    
    
    return X, X_symbol
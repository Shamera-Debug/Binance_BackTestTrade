
def clear_data():
    return None, 0, 0


def update_position(symbol, diff, cls_pred, asset, hist_price):
    # 포지션을 업데이트하는 로직
    if diff > 0.1 and cls_pred == 1:
        position_type = 'Long'  # 'Long' 포지션 진행
        purchase_amount = 200
        asset -= purchase_amount 
        print(f'{symbol}-Long -> 진입가격:{hist_price}')
    elif diff < -0.1 and cls_pred == 0:
        position_type = 'Short'  # 'Short' 포지션 진행
        purchase_amount = 200
        asset -= purchase_amount  
        print(f'{symbol}-Short -> 진입가격:{hist_price}')
    else:
        position_type = None  # 조건에 맞지 않으면 포지션을 열지 않음
        purchase_amount = 0
        print(f'{symbol}-진입 X')

    return position_type, purchase_amount, asset


def get_pnl(hist_price, real_price, position):
    if position == 'Long':
        return (real_price - hist_price) / hist_price * 10 
    else:  # position == 'Short'
        return (hist_price - real_price) / hist_price * 10 
    
    
def calculate(position_amount, change_rate):
    hist_fee = position_amount * 0.0005
    curr_price = position_amount * (1 + change_rate)
    curr_fee = curr_price * 0.0005
    
    return (curr_price - hist_fee - curr_fee)
    

def SL_TP(symbol, position_amount, hist_price, real_price, position, positions_count, asset, PROFIT, diff, cls_pred):
    change_rate = get_pnl(hist_price, real_price, position)
    if diff > 0.1 and cls_pred == 1:
        positions_count = positions_count - 1 
    elif diff < -0.1 and cls_pred == 0:
        positions_count = positions_count - 1 
        
    positions_count = positions_count + 1
    
    if positions_count == 5:
        temp_asset = calculate(position_amount, change_rate)
        asset += temp_asset
        PROFIT += temp_asset - position_amount
        
        print(f'{symbol}-{position} -> Start:{hist_price}, End:{real_price} -> Profit:{round(change_rate*100, 2)}%')
        position, position_amount, positions_count = clear_data()
    elif change_rate < -0.05:  # 손실률이 -5% 이하
        temp_asset = calculate(position_amount, change_rate)
        asset += temp_asset
        PROFIT += temp_asset - position_amount
        
        print(f'!!!!!{symbol}-{position} -> Start:{hist_price}, End:{real_price} -> Profit:{round(change_rate*100, 2)}%')
        position, position_amount, positions_count = clear_data()  
    else:
        print(f'{symbol}-{position} {5-positions_count}분 남음...')
        
    return position, position_amount, positions_count, asset , PROFIT


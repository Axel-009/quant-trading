# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 11:57:46 2018

@author: Administrator
"""

# In[1]:

# Updated to use yfinance (fix_yahoo_finance is deprecated)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf

# Import configuration and validators
try:
    from config import PREVIEW_DIR
    from validators import (
        get_validated_input,
        validate_ticker,
        validate_date,
        validate_date_range,
        validate_moving_average_period,
        validate_ma_pair,
        ValidationError
    )
    USE_VALIDATORS = True
except ImportError:
    print("Warning: config.py or validators.py not found. Using basic validation.")
    USE_VALIDATORS = False
    PREVIEW_DIR = 'preview'



# In[2]:

#simple moving average
def macd(signals):
    
    
    signals['ma1']=signals['Close'].rolling(window=ma1,min_periods=1,center=False).mean()
    signals['ma2']=signals['Close'].rolling(window=ma2,min_periods=1,center=False).mean()
    
    return signals



# In[3]:

#signal generation
#when the short moving average is larger than long moving average, we long and hold
#when the short moving average is smaller than long moving average, we clear positions
#the logic behind this is that the momentum has more impact on short moving average
#we can subtract short moving average from long moving average
#the difference between is sometimes positive, it sometimes becomes negative
#thats why it is named as moving average converge/diverge oscillator
def signal_generation(df,method):
    
    signals=method(df)
    signals['positions']=0

    #positions becomes and stays one once the short moving average is above long moving average
    signals['positions'][ma1:]=np.where(signals['ma1'][ma1:]>=signals['ma2'][ma1:],1,0)

    #as positions only imply the holding
    #we take the difference to generate real trade signal
    signals['signals']=signals['positions'].diff()

    #oscillator is the difference between two moving average
    #when it is positive, we long, vice versa
    signals['oscillator']=signals['ma1']-signals['ma2']

    return signals



# In[4]:

#plotting the backtesting result
def plot(new, ticker):
    
    #the first plot is the actual close price with long/short positions
    fig=plt.figure()
    ax=fig.add_subplot(111)
    
    new['Close'].plot(label=ticker)
    ax.plot(new.loc[new['signals']==1].index,new['Close'][new['signals']==1],label='LONG',lw=0,marker='^',c='g')
    ax.plot(new.loc[new['signals']==-1].index,new['Close'][new['signals']==-1],label='SHORT',lw=0,marker='v',c='r')

    plt.legend(loc='best')
    plt.grid(True)
    plt.title('Positions')
    
    plt.show()
    
    #the second plot is long/short moving average with oscillator
    #note that i use bar chart for oscillator
    fig=plt.figure()
    cx=fig.add_subplot(211)

    new['oscillator'].plot(kind='bar',color='r')

    plt.legend(loc='best')
    plt.grid(True)
    plt.xticks([])
    plt.xlabel('')
    plt.title('MACD Oscillator')

    bx=fig.add_subplot(212)

    new['ma1'].plot(label='ma1')
    new['ma2'].plot(label='ma2',linestyle=':')
    
    plt.legend(loc='best')
    plt.grid(True)
    plt.show()

    
# In[5]:

def main():

    #input the long moving average and short moving average period
    #for the classic MACD, it is 12 and 26
    #once a upon a time you got six trading days in a week
    #so it is two week moving average versus one month moving average
    #for now, the ideal choice would be 10 and 21

    global ma1,ma2,stdate,eddate,ticker,slicer

    #macd is easy and effective
    #there is just one issue
    #entry signal is always late
    #watch out for downward EMA spirals!

    print("=== MACD Oscillator 백테스팅 ===\n")

    try:
        if USE_VALIDATORS:
            # Use validated input
            ma1 = get_validated_input(
                'ma1 (단기 이동평균, 권장: 10): ',
                validate_moving_average_period
            )
            ma2 = get_validated_input(
                'ma2 (장기 이동평균, 권장: 21): ',
                validate_moving_average_period
            )
            validate_ma_pair(ma1, ma2)

            stdate = get_validated_input(
                '시작 날짜 (YYYY-MM-DD): ',
                validate_date
            )
            eddate = get_validated_input(
                '종료 날짜 (YYYY-MM-DD): ',
                validate_date
            )
            validate_date_range(stdate, eddate)

            ticker = get_validated_input('티커 심볼: ', validate_ticker)

            slicer = get_validated_input(
                '슬라이싱 (차트 표시할 데이터 시작점): ',
                validate_moving_average_period,
                min_val=0,
                max_val=10000
            )
        else:
            # Fallback to basic input
            ma1 = int(input('ma1:'))
            ma2 = int(input('ma2:'))
            stdate = input('start date in format yyyy-mm-dd:')
            eddate = input('end date in format yyyy-mm-dd:')
            ticker = input('ticker:')
            slicer = int(input('slicing:'))

        #downloading data
        print(f"\n데이터 다운로드 중: {ticker} ({stdate} ~ {eddate})...")
        df = yf.download(ticker, start=stdate, end=eddate, progress=False)

        if df.empty:
            raise ValueError(f"'{ticker}'에 대한 데이터를 가져올 수 없습니다. 티커를 확인해주세요.")

        print(f"✓ {len(df)}개의 데이터 포인트 다운로드 완료\n")

        new = signal_generation(df, macd)
        new = new[slicer:]
        plot(new, ticker)

        print("\n백테스팅 완료!")

    except ValidationError as e:
        print(f"\n❌ 입력 검증 오류: {e}")
        return
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return


#how to calculate stats could be found from my other code called Heikin-Ashi
# https://github.com/je-suis-tm/quant-trading/blob/master/heikin%20ashi%20backtest.py


if __name__ == '__main__':
    main()

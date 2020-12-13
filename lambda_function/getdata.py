#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import math
import os
import time
from datetime import datetime, timedelta, timezone

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
# from mpl_finance import candlestick_ohlc
# from mplfinance.original_flavor import candlestick_ohlc
from pandas import DataFrame, Series, concat, to_datetime

def get_data(period, size, from_date):
    """get_data
    cryptowatchから過去のohlcvsを取得

    Parameters
    ----------
    period : int
        ローソク足
    size : int
        取得件数

    Returns
    -------
    data : list
        data
    """

    url = "https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc"
    # url2 = "https://api.cryptowat.ch/markets/bitflyer/btcjpy/ohlc"

    try:
        if from_date != None:
            after = datetime.strptime(from_date, '%Y-%m-%d').timestamp()
        else:
            # start時間(UNIXTIME)を取得
            after = int(time.time()) - period * size

        query = {"periods": period, "after": int(after)}
        # print("cryptowatchから過去のohlcvsを取得：", query)
        #  date      , time  , open  , high  , low   , close       , volume
        # [1583618400, 985761, 987695, 983250, 986265, 496.73285044, 489989812.2301996],
        res = json.loads(requests.get(url, params=query).text)

        # 7番目の要素はdocsに記載がないので何なのか不明
        df = pd.DataFrame(res['result'][str(period)], columns=['date', 'open', 'high', 'low',
                                                        'close', 'volume', 'unknown']).dropna().drop(columns=['volume', 'unknown'])
        # print(df.head(3))

        # OANDAの分析データはこう
        # [['2016-01-03T22:00:00...00000000Z', '120.195', '120.235', '120.194', '120.227']]

        df['date'] = pd.to_datetime(df['date'], unit='s', utc=True)
        df.set_index('date', inplace=True)
        df.index = df.index.tz_convert('Asia/Tokyo')
        # print(df.head(3))

        return df.astype({'close': float, 'open': float, 'high': float, 'low': float})

    except Exception as e:
        print(dt_now(), " cryptowat接続エラー", e, url)
        raise e


def dt_now():
    return datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')


# 単純移動平均 (SMA)
def sma(ohlc: DataFrame, period=21) -> Series:
    return Series(
        ohlc['close'].rolling(period).mean(),
        name=f'SMA {period}',
    )

    # sma(df, 5).plot.line(color='y', legend=True)
    # sma(df, 10).plot.line(color='c', legend=True)
    # sma(df, 21).plot.line(color='m', legend=True)


# 指数平滑移動平均 (EMA)
def ema(ohlc: DataFrame, expo=21) -> Series:
    return Series(
        ohlc['close'].ewm(span=expo).mean(),
        name=f'EMA {expo}',
    )

    # ema(df, 5).plot.line(color='y', legend=True)
    # ema(df, 10).plot.line(color='c', legend=True)
    # ema(df, 21).plot.line(color='m', legend=True)


# 加重移動平均 (WMA)
def wma(ohlc: DataFrame, period: int = 9) -> Series:
    # WMA = ( 価格 * n + 価格(1) * n-1 + ... 価格(n-1) * 1) / ( n * (n+1) / 2 )
    denominator = (period * (period + 1)) / 2
    weights = Series(np.arange(1, period + 1)).iloc[::-1]

    return Series(
        ohlc['close'].rolling(period, min_periods=period).apply(lambda x: np.sum(weights * x) / denominator, raw=True),
        name=f'WMA {period}'
    )
    # wma(df, 5).plot.line(color='y', legend=True)
    # wma(df, 10).plot.line(color='c', legend=True)
    # wma(df, 21).plot.line(color='m', legend=True)


# 標準偏差
def sd(ohlc: DataFrame, period=10, ddof=0) -> float:
    return ohlc['close'].tail(period).std(ddof=ddof)

# >>> sd(df, ddof=0)
# 232.7845570479279
# >>> sd(df, ddof=1)
# 245.37646812828467


def plot(df):
    plt.style.use('ggplot')

    ax = plt.subplot()
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%D:%M', tz=timezone(timedelta(hours=9))))

    # candlestick_ohlc の第二引数に渡すタプルイテレータを生成
    # @see https://github.com/matplotlib/mpl_finance/blob/master/mpl_finance.py
    # quotes = zip(mdates.date2num(df.index), df['open'], df['high'], df['low'], df['close'])
    # candlestick_ohlc(ax, quotes, width=(1/24/len(df))*0.7, colorup='g', colordown='r')

    plt.show()



# タイムゾーンの生成
JST = timezone(timedelta(hours=+9), 'JST')


if __name__ == "__main__":
    import config.config as cfg
    import utility

    ex_pair = cfg.PRODUCT_CODE
    # ローソク足(秒で指定。1分足：60、5分足：300、900、1800、1h：3600、2h：7200、4h：14400、21600、43200、日足：86400、259200)
    PERIOD = utility.get_period(cfg.PERIOD)
    # OHLCV足の取得数
    SIZE = 6000

    from_date = None
    # from_date = '2009-01-02 19:12:00'
    df = get_data(PERIOD, SIZE, from_date)

    path = './simu/'
    os.makedirs(path, exist_ok=True)

    df.to_csv(path + ex_pair + '_' + str(PERIOD) + '.csv', encoding='UTF8')

    periods = [60, 300, 900, 1800, 3600, 7200, 21600, 43200]
    for p in periods:
        df = get_data(p, SIZE, from_date)
        df.to_csv(path + ex_pair + '_' + str(p) + '.csv', encoding='UTF8')

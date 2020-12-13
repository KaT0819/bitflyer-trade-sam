#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import math
import os
import time
from datetime import datetime, timedelta, timezone

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

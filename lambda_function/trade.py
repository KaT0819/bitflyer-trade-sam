#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import math
import os
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pybitflyer
import requests

import getdata
import mybitflyer
import strategy
import utility
from config import config as cfg

# タイムゾーンの生成
JST = timezone(timedelta(hours=+9), 'JST')

# 起動時刻退避
start_dt_now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

# インスタンスの作成
bitflyer = mybitflyer.MyBitflyerOrder(cfg.API_KEY, cfg.API_SECRET)


def lambda_handler(event, context):
    trade()

    return {'statusCode': 200,
            'body': {'success'},
            'headers': {'Content-Type': 'application/json'}}


def load_learn_data(ex_pair, period):
    """学習データの読み込み

    Arguments:
        ex_pair {[type]} -- [通貨ペア]
        period {[type]} -- [足]

    Returns:
        [type] -- [学習データ]
    """

    # 学習データ保存先（data/通貨ペア名 とする）
    save_dir = 'data/' + ex_pair + '/'
    save_file = 'parameter_' + str(period) + '.npz'
    save_path = save_dir + save_file

    if not os.path.exists(save_path):
        raise Exception("学習データがありません。" + save_path)
    # 学習したパラメータの読み込み
    # また、自身で実装された方は、指定のファイルを読み込んでください。
    return np.load(save_path)


def is_time_sleep(pos_size):
    """
    時間帯でポジションが無い場合にスリープする。
    """

    # 3時40分台 3時50分台
    if datetime.now(JST).hour == 3 and datetime.now(JST).minute >= 40 and pos_size == 0:
        print(dt_now(), "3時40分台でノーポジのため新規注文は送りません。")
        return True

    # 4時00分台
    if datetime.now(JST).hour == 4 and str(datetime.now(JST).strftime('%M'))[:1] == '0' and pos_size == 0:
        print(dt_now(), "4時00分台でノーポジのため新規注文は送りません。")
        return True

    return False


def notification(message):
    """
    外部へ状況送信
    """
    # Discord送信
    if cfg.DISCORD_URL != "":
        data = {"content": " " + message + " "}
        requests.post(cfg.DISCORD_URL, data=data)

    if cfg.SLACK_URL != "" and cfg.SLACK_TOKEN != "":
        headers = {'Authorization': 'Bearer {}'.format(cfg.SLACK_TOKEN)}
        data = {'channel': 'trade_bitflyer',
                'text': message.replace('@here', '<!here>')}
        # slack通知
        requests.post(cfg.SLACK_URL, headers=headers, json=data)


def my_makedirs(path):
    """
    ディレクトリの作成
    """

    if not os.path.isdir(path):
        os.makedirs(path)


def limit_order(pos_side, price, size, *args):
    """[注文API呼び出し]

    Arguments:
        pos_side {[type]} -- [BUY or SELL]
        price {[type]} -- [bid or ask]
        size {[type]} -- [size]
    """

    global bitflyer
    # 注文
    res = bitflyer.limit_order(pos_side, price, size)
    if res.get('status', 0) < 0:
        if res.get('status', 0) != -205:
            notification(dt_now() + " " + str(res))
        return

    msg = {pos_side: f"{price:,}", "size": size}
    print(dt_now(), str(args[0]), msg)
    # notification(dt_now() + " " + str(args[0]) + "：" + json.dumps(msg))
    # wait
    time.sleep(10)
    # 決済
    bitflyer.cancelAllOrder()


def is_order(position, change, order_size, ltp, collate):
    # 売買の切り替えありの場合
    if change == 1:
        return True

    # ポジションなしの場合、注文注文がありえる
    if position == 0:
        return True

    # 証拠金不足の場合
    if order_size * ltp > collate:
        print('証拠金不足のため注文しない', 'order:' + str(order_size * ltp), 'collate:' + str(collate))
        return False

    return True


def order(position, bid, ask, order_size, change, pos_size, pos_side):
    """[注文]

    Arguments:
        position {[type]} -- [ポジション持つかどうか。1：買い、0]
        bid {[type]} -- [買値]
        ask {[type]} -- [売値]
        order_size {[type]} -- [注文数]
        change {[type]} -- [description]
        pos_size {[type]} -- [BUY or SELL]
    """

    global bitflyer
    # 特別な場合だが、ショートポジから、ロングポジに切り替える場合
    # 以下、ポジション逆転に売買するため、positionと売買を逆転させている。s
    if change == 1:
        # 決済
        if pos_side == "BUY":
            # 決済売り注文
            # limit_order("SELL", ask-1, pos_size, '決済売り注文')
            print(dt_now(), '決済売り注文', pos_size)
            _ = bitflyer.market_order("SELL", pos_size)
        elif pos_side == "SELL":
            # 決済買い注文
            # limit_order("BUY", bid+1, pos_size, '決済買い注文')
            print(dt_now(), '決済買い注文', pos_size)
            _ = bitflyer.market_order("BUY", pos_size)

        if position == 1:
            # 買い注文
            # limit_order("BUY", bid+1, order_size, '買い替え買い注文')
            _ = bitflyer.market_order("BUY", pos_size)
            print(dt_now(), '買い替え買い注文', pos_size)
            notification(dt_now() + ' 買い替え買い注文')

        elif position == -1:
            # 売り注文
            # limit_order("SELL", ask-1, order_size, '買い替え売り注文')
            _ = bitflyer.market_order("SELL", pos_size)
            print(dt_now(), '買い替え売り注文', pos_size)
            notification(dt_now() + ' 買い替え売り注文')

    elif position == 1:
        # 新規買い注文
        # limit_order("BUY", bid+1, order_size, '新規買い注文')
        print(dt_now(), '新規買い注文', order_size)
        _ = bitflyer.market_order("BUY", order_size)

    elif position == -1:
        # 新規売り注文
        # limit_order("SELL", ask-1, order_size, '新規売り注文')
        print(dt_now(), '新規売り注文', order_size)
        _ = bitflyer.market_order("SELL", order_size)

    elif position == 0 and pos_size >= 0:
        # 決済
        if pos_side == "BUY":
            # 決済売り注文
            # limit_order("SELL", ask-1, pos_size, '決済売り注文')
            print(dt_now(), '決済売り注文', pos_size)
            _ = bitflyer.market_order("SELL", pos_size)
        elif pos_side == "SELL":
            # 決済買い注文
            # limit_order("BUY", bid+1, pos_size, '決済買い注文')
            print(dt_now(), '決済買い注文', pos_size)
            _ = bitflyer.market_order("BUY", pos_size)

    else:
        print(dt_now(), 'スルー')


def market_order(pos_side, pos_size):
    """[成行決済]

    Arguments:
        pos_side {[string]} -- [BUY or SELL]
        pos_size {[int]} -- [ポジション数]
    """

    global bitflyer
    if pos_side == "BUY":
        # 成行決済注文
        _ = bitflyer.market_order("SELL", pos_size)
    elif pos_side == "SELL":
        # 成行決済注文
        _ = bitflyer.market_order("BUY", pos_size)


def dt_now():
    return datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')


def trade():
    print(start_dt_now, "BOT開始")

    # --------------------------------------------------
    # iniファイルの読み込み
    # --------------------------------------------------
    LEVERAGE = cfg.LEVERAGE
    ORDER_LOT = cfg.ORDERLOT
    ORDER_MODE = cfg.ORDERMODE  # 1.固定ロット それ以外.レバレッジによる自動計算


    # 変数初期化
    start_collate = 0
    # tmp_colleate = 0
    # pos_sma = 0
    # breakout_flg = 0
    # max_mid_ohlcv = 0
    # min_mid_ohlcv = 0
    # past_stoch_d = 0
    # pylamid_flg = 0
    log_send_flg = 0

    period = utility.get_period(cfg.PERIOD)
    count = 6000

    # 取引を行う部分
    # 今回のプログラムにて使用する変数たち
    # ロングのとき'1'　ショートのとき'-1' ノーポジのとき'0'
    position = 0


    # ポジションを持った時の値を記録するためのクロックみたいなもの。詳しくは下記のwhile文を参照、
    change = 0

# トレード
# while True:

    minute = datetime.now(JST).minute

    change = 0
    # 通知メッセージ用
    msg = ""

    # ポジション取得
    try:
        # 建玉の一覧を取得（https://lightning.bitflyer.com/docs?lang=en#get-open-interest-summary）
        pos_side, pos_size, avg_price, sfd_valu, posmin, posmax, pos_collateral = bitflyer.get_pos()
        pos_size = round(pos_size, 2)
    except Exception as e:
        print(dt_now(), "API接続エラー get_pos", e)
        return

    try:
        # 証拠金の状態を取得（https://lightning.bitflyer.com/docs?lang=en#get-margin-status）
        # { "collateral": 100000,        # 預け入れた証拠金の評価額（円）
        #   "open_position_pnl": -715,   # 建玉の評価損益（円）
        #   "require_collateral": 19857, # 現在の必要証拠金（円）
        #   "keep_rate": 5.000}          # 現在の証拠金維持率
        collateral = bitflyer.getCollateral()
        pnl = collateral['open_position_pnl']  # 建玉の評価損益（円）
        collate = int(collateral['collateral'])  # 預け入れた証拠金の評価額（円）
        require_collate = int(collateral['require_collateral'])  # 現在の必要証拠金（円）
    except Exception as e:
        print(dt_now(), "API接続エラー getCollateral", e)
        return

    # 証拠金
    if start_collate == 0:
        start_collate = collate

    print(dt_now(), {"証拠金": f"{collate:,}", "損益": f"{int(pnl):,}", "pnl/collate": round(abs(pnl) / collate, 3), "pos_side": pos_side, 'pos_size': round(pos_size, 2), })
    # 損切
    if pnl < 0 and abs(pnl) / collate > cfg.LOSSCUTLINE:
        # 小数点2位まで切り捨て　roundだと切り上げる場合があるので、floor使用
        market_order(pos_side, math.floor(pos_size * 100) / 100)
        require_collate = 0
        print(dt_now(), '損切決済注文', f"{int(pnl):,}")
        notification(dt_now() + ' 損切決済注文：' + f"{int(pnl):,}")

    # 時間でポジションなしの場合は新規注文を送らない
    if is_time_sleep(pos_size):
        return

    # Ticker取得（https://lightning.bitflyer.com/docs?lang=ja#ticker）
    try:
        # 建玉の一覧を取得（https://lightning.bitflyer.com/docs?lang=en#get-open-interest-summary）
        tick = bitflyer.getTicker()
        msg = {"LTP": tick["ltp"], "volume": round(tick["volume"], 0), "best_bid": tick["best_bid"],
               "best_ask": tick["best_ask"]}
        # print(dt_now(), msg)
        # print(dt_now(), tick)
    except Exception as e:
        print(dt_now(), "API接続エラー ticker", e)
        return

    now_ltp = int(tick["ltp"])  # 最終取引価格
    best_bid = int(tick["best_bid"])
    best_ask = int(tick["best_ask"])
    # add += 1


    # 学習したパラメータの読み込み
    load_wbu = load_learn_data(cfg.PRODUCT_CODE, period)

    # 重みベクトルWの取得
    W = load_wbu['arr_0']
    # バイアスbの取得
    b = load_wbu['arr_1']
    # パラメタuの取得
    u = load_wbu['arr_2']

    try:
        df = getdata.get_data(period, count, None)
    except Exception as e:
        return

    bid, ask = df.close[-1] - 1.4*0.01, df.close[-1] + 1.4*0.01

    # 実際にパラメータの学習を行う。
    dd1, dd2, signal = strategy.execute(df)

    # 特徴データの作成
    x = np.array(signal[-1:])[0]
    # ポジションの取得
    dt = np.tanh(np.dot(W, x) + b + u * position)
    # 少し特別な処理
    if position != (dt > 0.6).astype(float) - (dt < -0.6).astype(float) and position != 0:
        change = 1

    # ポジション確認
    position = (dt > 0.6).astype(float) - (dt < -0.6).astype(float)

    # ロット
    if ORDER_MODE == 1:
        order_size = ORDER_LOT
    else:
        # 証拠金をもとに注文数を決める。
        n = 2  # 小数点桁数
        order_size = math.floor(((collate * LEVERAGE) / now_ltp) * 10 ** n ) /  (10 ** n)

    # ポジション可能な注文数に修正
    if pos_size > 0:
        if pos_side == "BUY" and position == -1:
            # order_size = round(order_size - pos_size, 2)
            # 追加注文しない
            return
        if pos_side == "SELL" and position == 1:
            # order_size = round(order_size - pos_size, 2)
            # 追加注文しない
            return
        if order_size < 0.01:
            print('注文数0.01以下')
            # order_size = 0.01
            return

    print(dt_now(), {"pos_side": pos_side, 'position': position, 'change': change, 'pos_size': pos_size, "価格": f"{avg_price:,}"
                    , 'bid': f"{best_bid:,}", 'ask': f"{best_ask:,}",

    })
    print(dt_now(), {'order_size': f"{order_size:,}", 'collate': f"{collate:,}", 'ltp': f"{now_ltp:,}",
                     'require_collate': f"{require_collate:,}"})

    # 利益確定 証拠金の10％を超えたら確定する。
    if pnl > collate * 0.1:
        # 小数点2位まで切り捨て　roundだと切り上げる場合があるので、floor使用
        market_order(pos_side, math.floor(pos_size * 100) / 100)
        print(dt_now(), '利益確定', f"{int(pnl):,}")
        notification(dt_now() + ' 利益確定：' + f"{int(pnl):,}")
        return

    # ポジションを持つかどうかの条件を判断するif文ゾーン
    if is_order(position, change, order_size, now_ltp, (collate - require_collate) * LEVERAGE):
        # 注文
        order(position, best_bid, best_ask, order_size, change, pos_size, pos_side)
        change = 0



    # ログ出力時間毎
    if minute % 60 != 0:
        log_send_flg = 0

    if minute % 60 == 0 and log_send_flg == 0:
        # msg = {"稼働時刻": start_dt_now, "稼働証拠金": f"{start_collate:,}", "現在証拠金": f"{collate:,}", "損益": f"{collate-start_collate:,}", "avg_price": f"{avg_price:,}",
        #       "pos_side": pos_side, "pos_size": round(pos_size, 8), "評価損益": pnl}
        msg = {"現在証拠金": f"{collate:,}", "損益": f"{collate-start_collate:,}",
               "評価損益": f"{int(pnl):,}", "pos_side": pos_side}

        print(dt_now(), msg)
        notification(json.dumps(msg, ensure_ascii=False))
        # cnt = 0

        # # 損益書き込み
        # my_makedirs('logs')

        # dt_log = datetime.now(JST).strftime('%Y-%m-%d')
        # f = open('logs/order_' + dt_log + '.log', 'a')
        # f.write(dt_now() + " " + json.dumps(msg, ensure_ascii=False) + '\n')
        # f.close()
        # log_send_flg = 1


if __name__ == "__main__":
    trade()

#!/usr/bin/python
# -*- coding: utf-8 -*-

import time

import pandas as pd
import numpy as np


def __init__(api_key, api_secret):
    # 初期化関数
    pass


def execute(df):
    # 実際にパラメータの学習を行う。
    dd = df.copy()

    # 使用するテクニカル指標を作成します。DataFrameでの処理をしていますので、分からない部分は随時ググってください。
    # ここでは、各テクニカル指標で使用する際の期間を列挙しています。なので、購入者の好みに合わせて期間を変更してください。
    para = [14, 12, 26, 9, 20, 25, 75, 200]
    # RSIの作成
    RSI = (100*dd.diff()[dd.diff() >= 0].fillna(0).rolling(window=para[0]).mean()/(dd.diff()[dd.diff() >= 0].fillna(
        0).rolling(window=para[0]).mean()+dd.diff()[dd.diff() < 0].abs().fillna(0).rolling(window=para[0]).mean())).close
    # MACDの作成
    SEMA = (dd.rolling(window=para[1]).mean()*(para[1]-1)+2*dd)/(para[1]+1)
    LEMA = (dd.rolling(window=para[2]).mean()*(para[2]-1)+2*dd)/(para[2]+1)
    MACD = (SEMA-LEMA).close
    MACD_s = (MACD.rolling(window=para[3]).mean(
    )*(para[3]-1)+2*MACD)/(para[3]+1)
    # ボリンジャーバンドの作成
    MA = dd.rolling(window=para[4]).mean().close
    bb_p = MA + 2*dd.rolling(window=para[4]).std().close
    bb_m = MA - 2*dd.rolling(window=para[4]).std().close
    # 指数平滑移動平均の作成：短期、中期、長期の三つ
    SEMA = ((dd.rolling(window=para[5]).mean(
    )*(para[5]-1)+2*dd)/(para[5]+1)).close.fillna(0)
    MEMA = ((dd.rolling(window=para[6]).mean(
    )*(para[6]-1)+2*dd)/(para[6]+1)).close.fillna(0)
    LEMA = ((dd.rolling(window=para[7]).mean(
    )*(para[7]-1)+2*dd)/(para[7]+1)).close.fillna(0)
    # これらのテクニカル指標のシグナルを入れておく入れ物
    all_sig = pd.DataFrame(index=dd.index)
    regu = 1
    # シグナルの生成
    # RSI：70以上、30以下、それ以外の３通り
    all_sig["RSI"] = (RSI > 70).astype(float) - (RSI < 30).astype(float)
    # MACD：シグナル線を突き抜ける瞬間が上下とそれ以外の３通り
    all_sig["MACD"] = ((MACD > MACD_s) & (MACD.shift() < MACD_s.shift())).astype(
        float) - ((MACD < MACD_s) & (MACD.shift() > MACD_s.shift())).astype(float)
    # BB：現在価格が、２σ線を上回る、−２σ線を下回るそれぞれの瞬間、各σ線を突き抜けている状態、それ以外の５通り
    all_sig['BB'] = ((bb_p < dd.close) & (bb_p.shift() > dd.close.shift())).astype(float) + (bb_p < dd.close).astype(
        float) - ((bb_m > dd.close) & (bb_m.shift() < dd.close.shift())).astype(float) - (bb_m > dd.close).astype(float)

    for i in range(6):
        # SEMA：5本分の指数平滑移動平均の変動幅
        all_sig['SEMA'+str(i)] = regu*(SEMA - SEMA.shift(i+1)).fillna(0)
        # MEMA：25本分の指数平滑移動平均の変動幅
        all_sig['MEMA'+str(i)] = regu*(MEMA - MEMA.shift(i+1)).fillna(0)
        # LEMA：75本分の指数平滑移動平均の変動幅
        all_sig['LEMA'+str(i)] = regu*(LEMA - LEMA.shift(i+1)).fillna(0)
        #    # 各時間での価格変動の追加
        #    all_sig['FLUC'+str(i)] = regu*(dd.close - dd.close.shift((i+1))).fillna(0)

    # 各時間での価格変動の追加
    for i in range(12):
        all_sig['FLUC'+str(i)] = regu*(dd.close -
                                       dd.close.shift((i+1))).fillna(0)

    # 少し長めの範囲の価格変動データも追加する
    num = [25, 75, 200]
    for i in num:
        # SEMA：5本分の指数平滑移動平均の変動幅
        all_sig['SEMA'+str(i)] = regu*(SEMA - SEMA.shift(i+1)).fillna(0)
        # MEMA：25本分の指数平滑移動平均の変動幅
        all_sig['MEMA'+str(i)] = regu*(MEMA - MEMA.shift(i+1)).fillna(0)
        # LEMA：75本分の指数平滑移動平均の変動幅
        all_sig['LEMA'+str(i)] = regu*(LEMA - LEMA.shift(i+1)).fillna(0)
        all_sig['FLUC'+str(i)] = regu*(dd.close -
                                       dd.close.shift((i+1))).fillna(0)

    # キリの良いデータ数にしておく
    signal = all_sig[len(dd) % 2000:].copy()
    dd1 = dd[len(dd) % 2000:].close.copy()

    # 価格変動の作成：ztの部分
    dd2 = regu*dd1.diff().fillna(0)

    return dd1, dd2, signal

def std():
    x = [8,12,16,20]
    np.std(x)

    
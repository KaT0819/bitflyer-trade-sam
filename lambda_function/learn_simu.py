#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime as dt
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

import config.config as cfg
import strategy
import utility

# 対象通貨ペア
ex_pair = cfg.PRODUCT_CODE
period = utility.get_period(cfg.PERIOD)

# 取得した時間足を指定
print('通貨ペア', ex_pair, '足', period)

# 繰り返し回数
epoch = 10
# 学習率
lr = 0.1
# 取引コスト(1000通貨：5.5円 ＋ スプレッド幅/2)：１通貨での取引コストに変換しています。
# c = 5.5*0.0001 + spread[ex_pair]/2
c = 0
# 使用する学習データの数
# あまり大きい数にしてしまうと、ものすごく時間がかかるので注意。
span = 2


# データ保存先
save_dir = 'autotrade/simu/'
save_file = ex_pair + '_' + str(period) + '.csv'
save_path = save_dir + save_file

# 学習データのダウンロード(このコードファイルと同じファイルに学習データも置いておいてください。読み込めませんので。)
df = pd.read_csv(save_path)
df.columns = ["date", "open", "high", "low", "close"]
df = df.set_index('date')
df.index = df.index.astype('datetime64[ns]')

# 実際にパラメータの学習を行う。
dd1, dd2, signal = strategy.execute(df)

# データセットを作る
# 上が学習用、下がテスト用
n_train = 1440*2*1
n_test = 720*1
# インデックスの入れ物を作る
train_index, test_index = [], []
# 学習データとテストデータのインデックスの取得
for i in range(0, len(dd1)-int(n_train/n_test)*n_test, n_test):
    train_index.append(dd1.index[i:i+n_train])
    test_index.append(dd1.index[i+n_train:(i+n_test)+n_train])

# ポジションの入れ物
Dt = np.zeros(n_train)
# 報酬関数の入れ物
Rt = np.zeros(n_train)
# 評価関数の定義
Ut = Rt.cumsum()

# テスト用の入れ物
ut = np.zeros((len(test_index), n_test))
dt = np.zeros(n_test)
rt = np.zeros(n_test)
# ポジションログを保存するためのもの
dt_log = []


# 学習していく

# 学習をスタートする期間の指定 ※0以上になるように！
# ここでは、最新のデータからspanの値分前の時点から学習をスタートする
nn = len(test_index)-span

# 学習部分
for j in tqdm(range(nn, nn+span)):
    print('\n\n', j+1-nn, '回目')
    # 重みとバイアスの初期化
    W = np.zeros(len(signal.columns))
    b = 0
    u = 0
    # 勾配の入れ物
    dW = np.zeros(len(W))
    db = np.zeros(1)
    du = np.zeros(1)
    dRt = np.zeros((n_train, 2, len(signal.columns)))
    dDt = np.zeros((n_train, len(signal.columns)))
    dDt_b = np.zeros(n_train)
    dDt_u = np.zeros(n_train)
    # 価格変動の取得：ztの部分
    train_dd = dd2[train_index[j]]
    # 学習のスタート
    for k in tqdm(range(epoch)):
        for i, t in tqdm(enumerate(train_index[j])):
            a = np.array(signal.loc[t])
            # ポジションと報酬の計算
            if i == 0:
                x = np.dot(W, a) + b
                Dt[i] = np.tanh(x)
                Dw, Db, Du = 0, 0, 0
            else:
                x = np.dot(W, a)+b+u*Dt[i-1]
                Dt[i] = np.tanh(x)
                Rt[i] = (train_dd[i]*Dt[i-1]-c*abs(Dt[i]-Dt[i-1]))
                # 評価関数の計算
                Ut[:i+1] = Rt[:i+1].cumsum()
                # 重み更新
                dDt[i] = a/np.cosh(x)**2 + u*dDt[i-1]/np.cosh(x)**2
                dDt_b[i] = 1/np.cosh(x)**2+u*dDt_b[i-1]/np.cosh(x)**2
                dDt_u[i] = Dt[i-1]/np.cosh(x)**2+u*dDt_b[i-1]/np.cosh(x)**2
                dRt[i][0] = -c*np.sign(Dt[i]-Dt[i-1])
                dRt[i][1] = train_dd[i] + c*np.sign(Dt[i]-Dt[i-1])
                dW = dRt[i][0]*dDt[i] + dRt[i][1]*dDt[i-1]
                db = -c*np.sign(Dt[i]-Dt[i-1])*dDt_b[i] + \
                    (train_dd[i] + c*np.sign(Dt[i]-Dt[i-1]))*dDt_b[i-1]
                du = -c*np.sign(Dt[i]-Dt[i-1])*dDt_u[i] + \
                    (train_dd[i] + c*np.sign(Dt[i]-Dt[i-1]))*dDt_u[i-1]
                # 普通の重み更新
                Dw += dW
                Db += db
                Du += du
        W += lr*Dw
        b += lr*Db
        u += lr*Du
        # コード実行時に、学習した結果による評価関数の収益の結果を出力してます。
        print(Ut[-1])
    # テストデータによる予測結果の計算
    # 価格変動の取得：ztの部分
    test_dd = dd2[test_index[j]]
    for i, t in tqdm(enumerate(test_index[j])):
        a = np.array(signal.loc[t])
        if i == 0:
            x = np.dot(W, a) + b + u*dt[-1]
            # この時、δの値が0.6を上回ればロング、-0.6を下回ればショートをとります。
            dt[i] = (np.tanh(x) > 0.7).astype(float) - \
                (np.tanh(x) < -0.7).astype(float)
            # 報酬関数の計算
            rt[i] = test_dd[i]*dt[-1] - c*abs(dt[i]-dt[-1])
        else:
            x = np.dot(W, a)+b+u*dt[i-1]
            # この時、δの値が0.6を上回ればロング、-0.6を下回ればショートをとります。
            dt[i] = (np.tanh(x) > 0.7).astype(float) - \
                (np.tanh(x) < -0.7).astype(float)
            # 報酬関数の計算
            rt[i] = test_dd[i]*dt[i-1]-c*abs(dt[i]-dt[i-1])
    # 評価関数の計算
    ut[j] = rt.copy()
    # ポジションログも保存しておきます。
    dt_log.append(dt.copy())


regu = 1
# ここでは、テストデータの予測結果を。グラフにプロットする。
# 画像が二つ保存されるので、その画像がけ予測結果になっています。
# １枚目が損益、２枚目がその時のポジションログを表しています。
plt.figure(figsize=(40, 30), dpi=250)
plt.rcParams["font.size"] = 44
plt.subplots_adjust(hspace=0.3)
n = 2
At = np.zeros(len(dd1.index[nn*n_test+n_train:n_train+n_test*(j+1)]))
At += 100*ut[nn:j+1].reshape(len(ut[nn:j+1])*n_test).cumsum()[:len(At)]/regu
plt.subplot(n, 1, 1)
plt.plot(dd1.index[nn*n_test+n_train:n_train+n_test*(j+1)], At, linewidth=5)
for i in range(nn, j):
    plt.axvline(dd1.index[nn*n_test+n_train:n_train+n_test*(j+1)]
                [n_test*(i+1-nn)], linewidth=0.5, linestyle='--', c='black')
plt.title('test profit : '+str(round(At[-1], 4))+'pips', fontsize=44*2)
plt.xticks(rotation=25)
plt.subplot(n, 1, 2)
plt.plot(dd1.index[nn*n_test+n_train:n_train+n_test*(j+1)], dd1[nn*n_test +
                                                                n_train:n_train+n_test*(j+1)], linewidth=5, c='r', label='test data')
plt.legend()
plt.xticks(rotation=25)
plt.savefig(save_dir + 'profit' + '_' + ex_pair +
            '_' + str(period) + '.png')
plt.close()

dt_log = np.array(dt_log).reshape(n_test*len(dt_log))
at = np.zeros(len(dd1.index[nn*n_test+n_train:n_train+n_test*(j+1)]))
at += dt_log[:len(at)]
plt.figure(figsize=(40, 30), dpi=250)
plt.rcParams["font.size"] = 44
plt.subplot(n, 1, 1)
plt.scatter(dd1.index[nn*n_test+n_train:n_train+n_test*(j+1)], at, s=50, c='g')
plt.title('test position', fontsize=44*2)
plt.xticks(rotation=25)
plt.subplot(n, 1, 2)
plt.plot(dd1.index[nn*n_test+n_train:n_train+n_test*(j+1)], dd1[nn*n_test +
                                                                n_train:n_train+n_test*(j+1)], linewidth=5, c='r', label='test data')
for i in range(nn, j):
    plt.axvline(dd1.index[nn*n_test+n_train:n_train+n_test*(j+1)]
                [n_test*(i-nn)], linewidth=0.5, linestyle='--', c='black')
plt.legend()
plt.xticks(rotation=25)
# plt.savefig(save_dir +'profit_posi' + '_' + ex_pair + '_' + str(period) + '.png')
plt.close()

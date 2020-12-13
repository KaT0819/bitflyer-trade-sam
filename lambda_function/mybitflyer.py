#!/usr/bin/python
# -*- coding: utf-8 -*-

import pybitflyer
import time

"""
bitFlyer注文用クラス
"""
class MyBitflyerOrder:

    symbol = 'FX_BTC_JPY'

    def __init__(self,api_key,api_secret):
        # 初期化関数
        self.public_api = pybitflyer.API()
        self.api = pybitflyer.API(api_key, api_secret)
        self.product_code = self.symbol

    def market_order(self, side, size, minute_to_expire=1):
        """
        指値注文関数
        :param side: 売買方向
        :param price: 価格
        :param size: 取引量
        :param minute_to_expire:注文寿命
        :return:
        """
        while True:
            res = self.api.sendchildorder(product_code=self.product_code, child_order_type="MARKET",
                                          minute_to_expire=minute_to_expire, side=side, size=size, price=0)
            error_status = res.get('status', 0)
            # print(res)
            if (error_status == -110):
                print('数量が少なすぎます:' + str(res))
                return res
            elif (error_status == -160):
                print('数量が大きいです:' + str(res))
                return res
            elif (error_status == -205):
                print('証拠金が足りないです:' + str(res))
                return res
            elif (error_status == -208):
                print('遅延エラー　リトライします:' + str(res))
                time.sleep(1)
            elif (res.get('status')):
                print({'その他エラーです': str(res), 'side': side, 'size': size, 'minute_to_expire': minute_to_expire})
                return res
            else:
                #print(side + ' limit order:price=' + str(price) + ',size=' + str(size) + ",res=" + str(res))
                return res

    def limit_order(self, side, price, size, minute_to_expire=1):
        """
        指値注文関数
        :param side: 売買方向
        :param price: 価格
        :param size: 取引量
        :param minute_to_expire:注文寿命
        :return:
        """
        while True:
            res = self.api.sendchildorder(product_code=self.product_code, child_order_type="LIMIT",
                                          minute_to_expire=minute_to_expire, side=side, size=size, price=price)
            error_status = res.get('status', 0)
            # print(res)
            if (error_status == -110):
                print('数量が少なすぎます:' + str(res))
                return res
            elif (error_status == -160):
                print('数量が大きいです:' + str(res))
                return res
            elif (error_status == -205):
                print('証拠金が足りないです:' + str(res))
                return res
            elif (error_status == -208):
                print('遅延エラー　リトライします:' + str(res))
                time.sleep(1)
            elif (res.get('status')):
                print('その他エラーです:' + str(res))
                return res
            else:
                #print(side + ' limit order:price=' + str(price) + ',size=' + str(size) + ",res=" + str(res))
                return res

    def get_pos(self):
        """
        建玉情報の取得関数
        :param product_code: 通貨種類
        :return:
        """
        side = ""
        size = 0
        avg_price = 0
        sfd_valu = 0
        posarr = []
        posmin = 0
        posmax = 0
        collateral = 0
        poss = self.api.getpositions(product_code=self.product_code)
        # もしポジションがあれば合計値を取得
        if len(poss) != 0:
            for pos in poss:
                side = pos["side"]
                size += pos["size"]
                avg_price += pos["size"] * pos["price"]
                if pos["sfd"] > 0:
                    sfd_valu += pos["size"] * pos["price"]
                if pos["size"] >= 0.01:
                    posarr.append(int(pos["price"]))
                collateral += float(pos["require_collateral"])
            avg_price = round(avg_price/size)
            if len(posarr) != 0:
                posmin = min(posarr)
                posmax = max(posarr)
        return side, size, avg_price, sfd_valu, posmin, posmax, collateral

    def cancelAllOrder(self):
        """
        注文取消関数
        :return:
        """
        self.api.cancelallchildorders(product_code=self.product_code)
        print("全注文をキャンセルしました")


    def getTicker(self):
        """
        ティッカー取得関数
        :return:
        """
        tick = self.api.ticker(product_code=self.product_code)
        return tick

    def getCollateral(self):
        """
        証拠金取得関数
        :return:
        """
        collateral = self.api.getcollateral()
        return collateral

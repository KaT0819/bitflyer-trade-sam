#!/usr/bin/python
# -*- coding: utf-8 -*-

"""設定の読み込み

Attributes:
    属性の名前 (属性の型): 属性の説明
    API_SECRET : string
        bitFlyerのAPIシークレットキー

"""

import os
import boto3

# SSMのシークレットキーの値を取得
def get_secure_parameter(param_key):
    ssm = boto3.client('ssm', region_name='ap-northeast-1')
    res = ssm.get_parameters(
        Names=[ param_key ],
        WithDecryption=True
    )

    return res['Parameters'][0]['Value']


# --------------------------------------------------
# AWSパラメータストアで定義。環境変数として値取得
# --------------------------------------------------
# ポジション確認ログを表示するか
PRODUCT_CODE = os.environ.get('product_code', 'FX_BTC_JPY')
ORDERLOT = float(os.environ.get('orderlot', 0.02))
LOSSCUTLINE = float(os.environ.get('LOSSCUT_LINE', 0.3))
ORDERMODE = int(os.environ.get('ORDER_MODE', 1))
LEVERAGE = float(os.environ.get('LEVERAGE', 4))
PERIOD = int(os.environ.get('PERIOD', 60))

# --------------------------------------------------
# bitFlyerのAPIkey読み込み
# --------------------------------------------------
API_KEY = get_secure_parameter(os.environ['API_KEY'])
API_SECRET = get_secure_parameter(os.environ['API_SECRET'])

# --------------------------------------------------
# 通知関係
# --------------------------------------------------
DISCORD_URL = get_secure_parameter(os.environ['DISCORD_URL'])
SLACK_URL = get_secure_parameter(os.environ['SLACK_URL'])
SLACK_TOKEN = get_secure_parameter(os.environ['SLACK_TOKEN'])

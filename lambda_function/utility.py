#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

# 取得した時間足を指定（60：1分、300：5分、600：10分、900：15分、1800：30分、3600：1時間、21600：6時間、43200：12時間、86400：1日）
period_data = {60, 300, 600, 900, 1800, 3600, 21600, 43200, 86400}


def get_period(default):
    """取得した時間足を指定
        引数で指定された値かコマンドの第一引数を返却する。
        指定可能なのはperiod_dataに定義された数値のみ
        （60：1分、300：5分、600：10分、900：15分、1800：30分、3600：1時間、21600：6時間、43200：12時間、86400：1日）

    Arguments:
        default {[string]} -- 時間足

    Returns:
        [string] -- 時間足
    """


    period = default
    if len(sys.argv) > 1:
        if int(sys.argv[1]) in period_data:
            period = int(sys.argv[1])

    return period



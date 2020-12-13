# bitflyer-trade-sam

Bitflyerの自動売買
SAMを用いてLambda関数をデプロイ


# install
## aws sam cli
``` shell
brew tap aws/tap
brew install aws-sam-cli
```

## python3
```
brew install python
```

https://www.python.org/downloads/



## python
``` shell

# 仮想環境設定
python3 -m venv venv
# 仮想環境有効化
source venv/bin/activate
# 環境変数登録
export PYTHONPATH=./:./service

# for Win
py -m venv venv
.\venv\Scripts\activate
$ENV:PYTHONPATH+="./;"

# 以降はmac、Win同様
# pip更新（初回のみ）
python -m pip install --upgrade pip
# ローカル実行用ライブラリインストール
pip install -r lambda_function/requirements.txt
# UT用ライブラリインストール
pip install boto3 pytest pytest-cov

```

### ディレクトリ構成
```bash
.
├── Makefile                    <-- Make to automate build 
├── README.md                   <-- This instructions file
├── lambda_function             <-- Lambda function code
│   ├── __init__.py
│   ├── app.py                  <-- Lambda function code
│   └── requirements.txt        <-- required lib
├── tests                       <-- Unit tests
├── venv                        <-- virtual env
├── env.json                    <-- SAM local用 環境変数
└── template.yaml               <-- SAM template
```



# デプロイ
## deploy
``` shell
cd python

make build

make deploy

```


## Cleanup
AWSへデプロイした場合、のクリア方法  
1．AWSのコンソールから削除  
1-1.コンソールにサインインし、CloudFormationのページを開く
1-2.スタックのページを開く
1-3.該当のスタック名を選択し、画面上部にある「削除」をクリック
  デプロイされた関連するAWSサービスの内容がすべて削除されます。

2．CLIによるコマンドでの削除  

```
cd python
make clean
```

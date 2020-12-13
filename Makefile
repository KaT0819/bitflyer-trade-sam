.PHONY: deploy

STACK_NAME  ?= bitflyer-trade-sam
PROFILE ?= default
ENDPOINT ?= http://localhost:4566
# SAMやAWSのコマンドの詳細なログを見たい場合はこちらのコメントを外す。
# DEBUG ?= --debug



build:
	sam build --use-container $(DEBUG)

deploy: build
	sam deploy -g --profile $(PROFILE) $(DEBUG)


clean:
	aws cloudformation delete-stack --stack-name $(STACK_NAME) --profile $(PROFILE) --region ap-northeast-1 $(DEBUG)


valid:
	sam validate --profile $(PROFILE)

local:
	sam local invoke BitflyerTradeSamFunction --event events/event.json


# test用のセットアップ。PYTHONPATHを通す
test-setup:
	: # Makefileからではpip以外のコマンドが有効にならなかったのでターミナルで下記コマンドを実行する。
	: # source ./venv/bin/activate
	: # export PYTHONPATH=./
	: # echo $PYTHONPATH
	: # pip install -r requirements.txt


test:
	pytest tests/ -v -s --cov=functions --cov=service --cov-report html
	: #  --cov-branch

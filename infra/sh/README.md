# Utility scripts

## zip-lambda.sh
```
sh ./zip-lambda.sh ../../lambda/fetch-match-stats-lambda
```

## create-stack.sh
```
sh ./create-stack.sh fetch-match-stats-lambda-stack \
../lambda/fetch-match-stats-lambda-template.json \
"ParameterKey=TABLEARN,ParameterValue=<table_arn> ParameterKey=TABLESTREAMARN,ParameterValue=<table_stream_arn>"
```

#!/bin/bash
STACK_NAME="$1"
STACK_PATH="$2"
PARAMS="$3"
aws cloudformation create-stack --stack-name $STACK_NAME --template-body file://$STACK_PATH --parameters $PARAMS --capabilities CAPABILITY_NAMED_IAM
#!/bin/bash
LAMBDA_PATH="$1"
echo $LAMBDA_PATH
cd ./$LAMBDA_PATH
zip -q -r -j package.zip * 

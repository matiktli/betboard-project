#!/bin/bash
LAMBDA_PATH="$1"
cd ./$LAMBDA_PATH
zip -q -r package.zip * 
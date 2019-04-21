#!/bin/sh
# marek kuczynski
# @marekq
# www.marek.rocks
# coding: utf-8

# create a variable with unix ts
ts=$(date +%s)

# zip the contents of the local dir excluding any git directories
zip -r serverless-cognito.zip . -x *.git* *.DS_Store* *.zip*

# copy the zip to an s3 bucket
aws s3 cp serverless-cognito.zip s3://marek-serverless/

# deploy the cloudformation template to us-east-1 with name 'cognitodemo-$ts'
aws cloudformation deploy --template template.yml --stack-name cognitodemo-$ts --capabilities CAPABILITY_IAM --region us-east-1

# after 1-2 minutes, you can retrieve the login url from the cloudformation output
echo 'created stack cognitodemo-'$ts

#!/bin/sh
# marek kuczynski
# @marekq
# www.marek.rocks
# coding: utf-8


# change this if you like
stackname='cognito'                         

# change to region of the deployment and s3 bucket
region='us-east-1'        

# the name where the serverless deployment artifacts will be stored, this must be precreated and in the same region
s3bucket='marek-serverless'                 


# don't edit anything below

# delete old lambda builds in local folder
rm ./*zip

# set the variable name for the artifact
ts=$(date +%s)
s3file='serverless-cognito-'$ts'.zip'

# zip the contents of the local dir excluding any git directories
zip -r $s3file . -x *.git* *.DS_Store* *.zip*

# copy the zip to your s3 bucket
aws s3 cp $s3file s3://$s3bucket

# deploy the cloudformation template to your account using the s3 artifact path as parameters
echo 'creating stack '$stackname' in region '$region
sam deploy --template-file template.yml --stack-name $stackname --region $region --capabilities CAPABILITY_IAM --parameter-overrides BucketName=$s3bucket CodeKey=$s3file

# after 1-2 minutes, you can retrieve the login url from the cloudformation output
echo 'created stack '$stackname' in region '$region'\n'
echo 'login url shown below'
aws cloudformation --region $region describe-stacks --stack-name $stackname --query 'Stacks[0].Outputs[0]'

# debug for marek - disabled by default
#aws s3 cp $s3file s3://marek-serverless/serverless-cognito.zip

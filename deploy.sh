#!/bin/sh
# marek kuczynski
# @marekq
# www.marek.rocks
# coding: utf-8

# set cli colors
RED='\033[0;31m'
NC='\033[0m'
dirn='./lambda/libs'
region='eu-west-1'

# rebuild the lambda package 
echo -e "\n${RED}@@@ downloading packages with pip3${NC}\n"
rm -rf $dirn && mkdir $dirn
pip3 install -r ./lambda/requirements.txt -t ./lambda/libs -U

# run sam validate to check the sam template
echo -e "\n${RED}@@@ running sam validate locally to test function${NC}\n"
sam validate

# run a local invoke to status page for testing
echo -e "\n${RED}@@@ running a GET request on local lambda using sam cli${NC}\n"
sam local invoke -e ./lambda/event/home.json
sam local invoke -e ./lambda/event/register.json

# check if samconfig.toml file is present
if [ ! -f samconfig.toml ]; then
    echo "no samconfig.toml found, starting guided deploy"
    sam deploy -g
else
    echo "samconfig.toml found, proceeding to deploy"
    sam deploy
fi

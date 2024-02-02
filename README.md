Public exposure Review

How to get Started

prerequisite

aws access env variable should be set or aws cli is configured
python 3.X should be present

Steps

git clone <>

python -m pip install -r requirements.txt or 
pip install -r requirements.txt

Usage

usage: main.py [-h] [-sgs SGS] [-region REGION]

options:
  -h, --help      show this help message and exit
  -sgs SGS        sg-isdgfd,sg-sdgdsfg
  -region REGION  us-east-1

example 

python main.py -sgs sg-isdgfd,sg-sdgdsfg -region us-east-1



Note: First run on a day may take time as it will fetch all the data and cache on filesystem 


Ideas




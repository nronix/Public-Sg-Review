
# Public Expsoure Review

A Helpfull utility to create interactive visualization of the AWS Infrastructure exposed to public internet. 




## Installation

Python Required

```bash
  git clone https://github.com/nronix/Public-Sg-Review.git
  cd Public-Sg-Review
  python -m pip install -r requirements.txt
```
    
## Documentation

usage: main.py [-h] [-sgs SGS] [-region REGION]

options: 
-h, --help show this help message and exit
-sgs SGS sg-isdgfd,sg-sdgdsfg 
-region REGION us-east-1
-out filename

example  
``` 
python main.py -sgs aba -region ap-south-1 -out filename 
```



## Demo

![image](https://github.com/nronix/Public-Sg-Review/assets/22999507/cf3155bf-dd9d-4fc0-98de-b5cf813c87c0)



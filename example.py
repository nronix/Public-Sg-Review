import boto3
import subprocess
regions = ["ap-south-1"]

if __name__ == "__main__":
    for region in regions:
        session = boto3.session.Session(region_name=region)
        client = session.client('ec2')
        sgs = client.describe_security_groups()
        public_sg = set()
        for sg in sgs['SecurityGroups']:
            ip_permissions = sg["IpPermissions"]
            for perm in ip_permissions:
                for ip in perm["IpRanges"]:
                    if "0.0.0.0/0" == ip['CidrIp']:
                        public_sg.add(sg['GroupId'])
        subprocess.call("python main.py -sgs {} -region {} -out {}".format(",".join(public_sg),region,region), shell=True)
        print(public_sg)
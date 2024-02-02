from os.path import isfile
from json import loads,dumps


class RDS:
    PATH = "cache/rds_cache.json"

    def __init__(self, client,use_cache=True):
        self.client = client
        self.rds_data = None
        if isfile(self.PATH) and use_cache:
            self.rds_data = loads(open(self.PATH).read())
        else:
            self.rds_data = self.describe_rds()

    def describe_rds(self):
        if self.rds_data is not None:
            return self.rds_data
        result = []
        response = self.client.describe_db_instances()
        print(response)
        result.extend(response['DBInstances'])
        while "Marker" in response.keys():
            response = self.client.describe_db_instances(Marker=response['Marker'])
            result.extend(response['DBInstances'])
        out = open(self.PATH,"w")
        out.write(dumps(result,default=str))
        out.close()
        return result

    def get_rds_filter_sg(self, sg_id):
        results = []

        for rds in self.rds_data:
            match = False
            temp = dict()
            temp['sgs'] = []
            for vpc_sg in rds['VpcSecurityGroups']:
                if vpc_sg['VpcSecurityGroupId'] == sg_id:
                    match=True
                    temp['sgs'].append(vpc_sg['VpcSecurityGroupId'])
            if match:
                temp['name'] = rds['DBInstanceIdentifier']
                temp['engine'] = rds['Engine']
                temp['address'] = rds['Endpoint']['Address']
                temp['port'] = rds['Endpoint']['Port']
                temp['vpcid'] = rds['DBSubnetGroup']['VpcId']
                temp['public'] = rds['PubliclyAccessible']
                results.append(temp)
        return results

    def get_rds_by_ip(self,ip,sg_id):
        scope = self.get_rds_filter_sg(sg_id)
        import socket
        for rds in scope:
            ips_found = socket.gethostbyname_ex(rds['address'])[2]
            print(ips_found)
            if ip in ips_found:
                return rds

from os.path import isfile
from json import loads, dumps


class Redshift:
    redshift_data = None
    PATH = "cache/redshift_cache.json"

    def __init__(self, client, use_cache=True):
        self.client = client
        if isfile(self.PATH) & use_cache:
            self.redshift_data = loads(open(self.PATH).read())
        else:
            self.redshift_data = self.describe_redshift()

    def describe_redshift(self):
        if self.redshift_data:
            return self.redshift_data
        result = []
        response = self.client.describe_clusters()
        result.extend(response['Clusters'])
        while "Marker" in response.keys():
            response = self.client.describe_clusters(Marker=response['Marker'])
            result.extend(response['Clusters'])
        out = open(self.PATH, "w")
        out.write(dumps(result, default=str))
        out.close()
        self.redshift_data = result

    def get_redshift_filter_sg(self, sg_id):
        results = []
        for redshift in self.redshift_data:
            match = False
            temp = dict()
            temp['sgs'] = []
            for vpc_sg in redshift['VpcSecurityGroups']:
                if vpc_sg['VpcSecurityGroupId'] == sg_id:
                    match = True
                    temp['sgs'].append(vpc_sg['VpcSecurityGroupId'])
            if match:
                temp['name'] = redshift['ClusterIdentifier']
                temp['address'] = redshift['Endpoint']['Address']
                temp['port'] = redshift['Endpoint']['Port']
                temp['vpcid'] = redshift['VpcId']
                temp['public'] = redshift['PubliclyAccessible']
                results.append(temp)
        return results

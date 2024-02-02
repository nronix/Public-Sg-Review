from os.path import isfile
from json import loads, dumps


class NLB:
    nlb_data = None
    PATH = "cache/nlb_cache.json"

    def __init__(self, client, use_cache=True):
        self.client = client
        if isfile(self.PATH) & use_cache:
            self.nlb_data = loads(open(self.PATH).read())
        else:
            self.nlb_data = self.describe_nlb()

    def describe_nlb(self):
        if self.nlb_data:
            return self.nlb_data
        temp = []
        response = self.client.describe_load_balancers()
        self.add_nlb_only(response, temp)
        while 'NextMarker' in response.keys():
            response = self.client.describe_load_balancers(Marker=response['NextMarker'])
            self.add_nlb_only(response, temp)
        self.nlb_data = temp
        out = open(self.PATH, "w")
        out.write(dumps(temp, default=str))
        out.close()
        return temp

    def describe_nlb_listeners(self, lb_arn):
        response = self.client.describe_listeners(LoadBalancerArn=lb_arn)
        t = []
        for listener in response['Listeners']:
            for action in listener['DefaultActions']:
                if action['Type'] == "forward":
                    listener['TargetHealthDescriptions'] = self.describe_nlb_target_health(action['TargetGroupArn'])
                    t.append(listener)
        return t

    def describe_nlb_target_health(self, target_arn):
        return self.client.describe_target_health(TargetGroupArn=target_arn)['TargetHealthDescriptions']

    def add_nlb_only(self,data, temp):
        for nlb in data['LoadBalancers']:
            if nlb['Type'] == 'network' and nlb['Scheme'] == 'internet-facing':
                nlb_dict = dict()
                nlb_dict["lb_arn"] = nlb['LoadBalancerArn']
                nlb_dict['dns_name'] = nlb['DNSName']
                nlb_dict['lb_name'] = nlb['LoadBalancerName']
                nlb_dict['vpc_id'] = nlb['VpcId']
                nlb_dict['targets'] = []
                listeners = self.describe_nlb_listeners(nlb['LoadBalancerArn'])

                for listener in listeners:
                    b = dict()
                    b['port'] = listener['Port']
                    b['protocol'] = listener['Protocol']
                    b['instances'] = []
                    for health in listener['TargetHealthDescriptions']:
                        a = dict()
                        a['id'] = health['Target']['Id']
                        a['status'] = health['TargetHealth']['State']
                        b['instances'].append(a)
                    nlb_dict['targets'].append(b)

                temp.append(nlb_dict)
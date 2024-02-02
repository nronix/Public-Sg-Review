class ELB:
    cache = {}
    cache_target = {}
    cache_target_health = {}

    def __init__(self, client):
        self.client = client

    def describe_elb(self, name):
        if name not in self.cache.keys():
            response = self.client.describe_load_balancers(LoadBalancerNames=[name, ])['LoadBalancerDescriptions'][0]
            self.cache[name] = response
        else:
            response = self.cache[name]

        return self.process_elb(response)

    @staticmethod
    def process_elb(elb_data):
        temp = dict()
        temp['elb_name'] = elb_data['LoadBalancerName']
        temp['elb_dnsname'] = elb_data['DNSName']
        temp['elb_instances'] = []
        for instance in elb_data['Instances']:
            temp['elb_instances'].append(instance['InstanceId'])

        return temp

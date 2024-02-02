class ELBV2:
    cache = {}
    cache_target = {}
    cache_target_health = {}

    def __init__(self, client):
        self.client = client

    def describe_elb(self, name):
        if name not in self.cache.keys():
            response = self.client.describe_load_balancers(Names=[name, ])['LoadBalancers'][0]
            self.cache[name] = response
        else:
            response = self.cache[name]
        response['TargetGroups'] = self.describe_targets(response['LoadBalancerArn'])
        return self.process_elb(response)

    def describe_targets(self, lb_arn):
        if lb_arn in self.cache_target.keys():
            response = self.cache_target[lb_arn]
        else:
            response = self.client.describe_target_groups(LoadBalancerArn=lb_arn)['TargetGroups']
            self.cache_target[lb_arn] = response
        temp = []
        for target in response:
            target['TargetGroupHealth'] = self.describe_target_health(target['TargetGroupArn'])
            temp.append(target)

        return temp

    def describe_target_health(self, target_arn):
        if target_arn in self.cache_target_health.keys():
            response = self.cache_target_health[target_arn]
        else:
            response = self.client.describe_target_health(TargetGroupArn=target_arn)['TargetHealthDescriptions']
            self.cache_target_health[target_arn] = response
        return response

    @staticmethod
    def process_elb(elb_data):
        temp = dict()
        temp['elb_name'] = elb_data['LoadBalancerName']
        temp['elb_arn']  = elb_data['LoadBalancerArn']
        temp['elb_dnsname'] = elb_data['DNSName']
        temp['elb_targets'] = []
        for target in elb_data['TargetGroups']:
            for tg_health in target['TargetGroupHealth']:
                t = dict()
                if tg_health['Target']['Id'].startswith('i-'):
                     t['type'] = "ec2"
                else:
                    t['type'] = "eni"
                t['id'] = tg_health['Target']['Id']
                t['port'] = tg_health['Target']['Port']
                t['health'] = tg_health['TargetHealth']['State']
                temp['elb_targets'].append(t)
        return temp
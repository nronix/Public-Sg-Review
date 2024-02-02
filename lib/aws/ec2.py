class EC2:
    cache_ec2 = {}
    cache_sg = {}
    cache_subnet = {}
    cache_vpc = {}

    def __init__(self, client):
        self.client = client

    def describe_ec2(self, instance_id):
        if instance_id in self.cache_ec2.keys():
            response = self.cache_ec2[instance_id]
        else:
            response = self.client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]
            self.cache_ec2[instance_id] = response
        return response

    def describe_subnet(self, subnet_id):
        if subnet_id in self.cache_subnet.keys():
            return self.cache_subnet[subnet_id]
        else:
            response =  self.client.describe_subnets(SubnetIds=[subnet_id,])["Subnets"][0]
            self.cache_subnet[subnet_id] = response
            return response

    def describe_sgs(self, id):
        if id in self.cache_sg.keys():
            return self.cache_sg[id]
        else:
            response = self.client.describe_security_groups(GroupIds=[id])['SecurityGroups'][0]
            self.cache_sg[id] = response
            return response

    def describe_network_interface(self, sg):
        response = self.client.describe_network_interfaces(Filters=[
            {
                'Name': 'group-id',
                'Values': [
                    sg,
                ]
            }])
        return self.process_enis(response)

    @staticmethod
    def process_enis(response):
        enis = []
        for eni in response['NetworkInterfaces']:
            eni_obj = dict()
            eni_obj['id'] = eni['NetworkInterfaceId']
            eni_obj['public_ip'] = None
            if 'Association' in eni.keys():
                if 'PublicIp' in eni["Association"].keys():
                    eni_obj['public_ip'] = eni["Association"]["PublicIp"]
            eni_obj['description'] = eni['Description']
            eni_obj['interface_type'] = eni['InterfaceType']
            if "InstanceId" in eni['Attachment'].keys():
                eni_obj['instance_id'] = eni['Attachment']['InstanceId']
            else:
                eni_obj['instance_id'] = None

            eni_obj['status'] = eni['Status']
            eni_obj['subnet_id'] = eni['SubnetId']
            eni_obj['vpc_id'] = eni['VpcId']
            eni_obj['private_ip'] = eni['PrivateIpAddress']
            eni_obj['groups'] = eni['Groups']

            enis.append(eni_obj)
        return enis

    def describe_vpc(self,vpc_id):
        if vpc_id in self.cache_vpc.keys():
            return self.cache_vpc[vpc_id]
        else:
            response = self.client.describe_vpcs(VpcIds=[ vpc_id, ], )['Vpcs'][0]
            self.cache_vpc[vpc_id] = response
            return response

    @staticmethod
    def get_name_from_tag(ec2_data):
        if "Tags" in ec2_data.keys():
            for tag in ec2_data['Tags']:
                if tag['Key'].lower() == 'name':
                    return tag['Value']
        if "InstanceId" in ec2_data.keys():
            return ec2_data['InstanceId']
        if "SubnetId" in ec2_data.keys():
            return ec2_data['SubnetId']
        if "VpcId" in ec2_data.keys():
            return ec2_data['VpcId']
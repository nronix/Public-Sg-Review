import json
import argparse
import boto3
from lib.aws.ec2 import EC2
from lib.aws.elbv2 import ELBV2
from lib.aws.elb import ELB
from lib.aws.rds import RDS
from lib.aws.redshift import Redshift
from lib.node import ViZNode
from lib.helper import find_ports
from lib.aws.nlb import NLB


def create_link(ports, sg_id, sg_name):
    if len(ports) == 1 and ports[0] in [80, 443]:
        type_a = "cloud_http"
    elif len(ports) == 2 and (ports[0] in [80, 443] and ports[1] in [80, 443]):
        type_a = "cloud_http"
    else:
        type_a = "cloud"
    return {
        "id": sg_id,
        "name": "Allow Public Traffic from port",
        "type": type_a,
        "local_id": sg_id,
        "node_data": {sg_name: ports}}


def evaluate_interfaces(session, eni_nodes, sg_id):
    ec2_helper = EC2(session.client('ec2'))
    elb_helper = ELBV2(client=session.client("elbv2"))
    for interface in ec2_helper.describe_network_interface(sg_id):

        if interface['interface_type'] == 'interface':
            # find the type of interface RDS, EC2 or ELB

            if interface['instance_id'] is not None:
                if interface['public_ip'] is None:
                    print("Public Ip not Attached to ENI,Checking for possible public exposure via NLB")
                    evaluate_nlb(session, eni_nodes, ec2_helper, interface['instance_id'],sg_id)
                else:
                    ec2_data = ec2_helper.describe_ec2(interface['instance_id'])
                    eni_nodes.add_data_to_node(interface['instance_id'], ec2_helper.get_name_from_tag(ec2_data), "ec2",
                                               ec2_data['SubnetId'], ec2_data)
                    # add subnet node only when a new ec2 instance is found
                    subnet_data = ec2_helper.describe_subnet(ec2_data['SubnetId'])
                    eni_nodes.add_data_to_node(subnet_data['SubnetId'], ec2_helper.get_name_from_tag(subnet_data),
                                               "subnet",
                                               subnet_data['VpcId'],
                                               node_data=subnet_data)
                    eni_nodes.add_edge_data(sg_id, interface['instance_id'], [])

            elif "elb app" in interface['description'].lower():

                lb_data = elb_helper.describe_elb(interface['description'].split("/")[1])
                eni_nodes.add_data_to_node(lb_data['elb_arn'], lb_data['elb_name'], "elb", interface['vpc_id'],
                                           node_data=lb_data)
                # Add connection between LB and internet
                eni_nodes.add_edge_data(sg_id, lb_data['elb_arn'], [])

                for elb_target in lb_data['elb_targets']:
                    if elb_target['type'] == "ec2":
                        ec2_data = ec2_helper.describe_ec2(elb_target['id'])

                        # icon color will change based on health
                        type_of = "ec2_unhealthy" if elb_target['health'] == "unhealthy" else "ec2"
                        eni_nodes.add_data_to_node(elb_target['id'], ec2_helper.get_name_from_tag(ec2_data), type_of,
                                                   ec2_data['SubnetId'],
                                                   ec2_data)
                        # add subnet only for new ec2
                        subnet_data = ec2_helper.describe_subnet(ec2_data['SubnetId'])
                        eni_nodes.add_data_to_node(subnet_data['SubnetId'], ec2_helper.get_name_from_tag(subnet_data),
                                                   "subnet",
                                                   subnet_data['VpcId'],
                                                   node_data=[])
                    else:
                        # backend isn't probably an ec2 instance
                        # TODO improve to detect backend type
                        eni_nodes.add_data_to_node(elb_target['id'], "Unknown Ip", "ec2_unhealthy",
                                                   interface['subnet_id'],
                                                   [])
                    # add an edge between load balancer and Backend
                    eni_nodes.add_edge_data(lb_data['elb_arn'], elb_target['id'], elb_target)
            # Classic Load balancer
            elif "elb" in interface['description'].lower():
                lb_name = interface['description'].split(" ")[1]
                elbv1_helper = ELB(session.client('elb'))
                lb_data = elbv1_helper.describe_elb(lb_name)
                eni_nodes.add_data_to_node(lb_data['elb_name'], lb_data['elb_name'], "elb", interface['vpc_id'],
                                           node_data=lb_data)
                for instance in lb_data['elb_instances']:
                    ec2_data = ec2_helper.describe_ec2(instance)
                    eni_nodes.add_data_to_node(instance, ec2_helper.get_name_from_tag(ec2_data), "ec2",
                                               ec2_data['SubnetId'], ec2_data)
                    # add subnet only for ec2
                    subnet_data = ec2_helper.describe_subnet(ec2_data['SubnetId'])
                    eni_nodes.add_data_to_node(subnet_data['SubnetId'], ec2_helper.get_name_from_tag(subnet_data),
                                               "subnet",
                                               subnet_data['VpcId'],
                                               node_data=[])
                    eni_nodes.add_edge_data(lb_data['elb_name'], instance, [])
                # add sg to lb node
                eni_nodes.add_edge_data(sg_id, lb_data['elb_name'], [])
            elif "rds" in interface['description'].lower():
                rds_helper = RDS(session.client('rds'))
                if interface['public_ip'] is None:
                    print("Public Ip not Attached to ENI,Checking for possible public exposure via NLB")
                    #evaluate_rds(session, eni_nodes, sg_id)
                    evaluate_nlb_ip(session,eni_nodes,interface['private_ip'],rds_helper,sg_id)
                else:
                    evaluate_rds(rds_helper, eni_nodes, sg_id)
            elif "redshift" in interface['description'].lower():
                if interface['public_ip'] is None:
                    print("Public Ip not Attached to ENI,Checking for possible public exposure via NLB")
                else:
                    evaluate_redshift(session, eni_nodes, sg_id)
            else:
                print("New ENI Type Discovered Please implement the logic {}".format(interface['id']))
        else:
            # Currently we have implement only for interface Type
            pass
    return eni_nodes


def evaluate_rds(rds_helper, rds_nodes, sg_ids):

    rds_data = rds_helper.get_rds_filter_sg(sg_ids)
    for rds in rds_data:
        rds_nodes.add_data_to_node(rds['name'], rds['name'], "rds", rds['vpcid'], rds)
        rds_nodes.add_edge_data(sg_ids,rds['name'],[])
    return rds_helper


def evaluate_redshift(session, redshift_nodes, sg_id):
    redshift_helper = Redshift(session.client('redshift'))
    for redshift in redshift_helper.get_redshift_filter_sg(sg_id):
        redshift_nodes.add_data_to_node(redshift['name'], redshift['name'], "redshift", redshift['vpcid'], redshift)
        redshift_nodes.add_edge_data(sg_id, redshift['name'], [])


def evaluate_nlb(session, nlb_nodes,ec2_helper,id, sg_id):
    nlb_helper = NLB(session.client('elbv2'))
    nlb_data = nlb_helper.nlb_data
    for nlb in nlb_data:
        found = False
        for target in nlb['targets']:
            for instance in target["instances"]:
                if id == instance['id']:
                    found = True
                    ec2_data = ec2_helper.describe_ec2(instance['id'])
                    nlb_nodes.add_data_to_node(instance['id'], ec2_helper.get_name_from_tag(ec2_data), "ec2",
                                               ec2_data['SubnetId'], ec2_data)
                    subnet_data = ec2_helper.describe_subnet(ec2_data['SubnetId'])
                    nlb_nodes.add_data_to_node(subnet_data['SubnetId'], ec2_helper.get_name_from_tag(subnet_data),
                                               "subnet",
                                               subnet_data['VpcId'],
                                               node_data=[])
                    nlb_nodes.add_edge_data(nlb['lb_arn'], instance['id'], target)
        if found:
            nlb_nodes.add_edge_data(sg_id,nlb['lb_arn'],nlb['targets'])
            nlb_nodes.add_data_to_node(nlb['lb_arn'], nlb['lb_name'], "nlb", nlb['vpc_id'], nlb)


def evaluate_nlb_ip(session, nlb_nodes,ip_id,rds_helper,sg_id):
    nlb_helper = NLB(session.client('elbv2'))
    nlb_data = nlb_helper.nlb_data
    for nlb in nlb_data:
        found = False
        for target in nlb['targets']:
            for instance in target["instances"]:
                if ip_id == instance['id']:
                    found = True
                    rds_data = rds_helper.get_rds_by_ip(instance['id'],sg_id)
                    nlb_nodes.add_data_to_node(rds_data['name'], rds_data['name'], "rds",
                                               rds_data['vpcid'], rds_data)
                    nlb_nodes.add_edge_data(nlb['lb_arn'], rds_data['name'], target)
        if found:
            nlb_nodes.add_edge_data(sg_id,nlb['lb_arn'],nlb['targets'])
            nlb_nodes.add_data_to_node(nlb['lb_arn'], nlb['lb_name'], "nlb", nlb['vpc_id'], nlb)


def main(session, sg_ids):
    ec2_helper = EC2(session.client('ec2'))
    # sts = session.client('sts')
    init_nodes = ViZNode()
    account_id = "899991151204"  # sts.get_caller_identity()['Account']
    region = session.region_name
    init_nodes.add_data_to_node(account_id, account_id, "account", "", [])
    init_nodes.add_data_to_node(region, region, "region", account_id, [])
    for sg in sg_ids:
        sg_data = ec2_helper.describe_sgs(sg)
        ports = find_ports(sg_data)
        if ports:
            init_nodes.add_dict_to_node(create_link(ports, sg_data['GroupId'], sg_data['GroupName']))
            vpc_data = ec2_helper.describe_vpc(sg_data['VpcId'])
            init_nodes.add_data_to_node(vpc_data['VpcId'], ec2_helper.get_name_from_tag(vpc_data), 'vpc', region,
                                        vpc_data)
            evaluate_interfaces(session, init_nodes, sg)
    return init_nodes


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-sgs", help="sg-isdgfd,sg-sdgdsfg")
    parser.add_argument("-region", help="us-east-1")
    parser.add_argument("-out",help="File name to write output",default="data")
    args = parser.parse_args()
    sgs = args.sgs.split(",")
    aws_session = boto3.session.Session(region_name=args.region)
    diagram_nodes = main(aws_session, sgs)
    out = open("ui/web/sg_review/{}.json".format(args.out), "w")
    print(diagram_nodes.get_nodes())
    out.write(json.dumps(diagram_nodes.get_nodes(), default=str))
    out.close()

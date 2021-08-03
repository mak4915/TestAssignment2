#!/usr/bin/env python
import boto3
import argparse

def get_account_number():
    """get_account_number() -
    gets the number of current account (necessary for ARN).
    """
    client = boto3.client('iam')
    account_number = client.get_user()['User']['Arn'].split(':')[4]
    return account_number


def create_arn(service, region, name):
    """create_arn(service, region, name) -
    creates arn for an object 'name' in a specify 'region' for selected
    'service'.
    """
    account_number = get_account_number()
    arn = 'arn:aws:%s:%s:%s:db:%s' % (service, region, account_number, name)
    return arn


def check_response(content):
    """check_response(content) -
    checks that return content is OK (HTTP response 200).
    """
    status = content['ResponseMetadata']['HTTPStatusCode']
    if status == 200:
        return True
    else:
        return False

def tag_object(name, tag, otype, region):
    """tag_object(name, tag, otype, region) -
    tags object 'name' (in selected 'region' with 'tag' (tuple, in future
    maybe list or tuple). An AWS object type i.e. RDS, EC2, S3. of the
    object is specify by 'otype'.
    """
    conn = boto3.client(otype)
    print tag[0]
    tag = [{'Key':tag[0], 'Value':tag[1]}]
    # EC2
    if otype == 'ec2':
        response = conn.describe_instances(Filters=\
                [{'Name':'tag-value', 'Values':[name]}])
        if check_response:
            instance_ids = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_ids.append(instance['InstanceId'])
                    conn.create_tags(Resources=instance_ids, Tags=new_tag)
    # ELB
    elif otype == 'elb':
        conn.add_tags(LoadBalancerNames=[name], Tags=new_tag)
    # ASG
    elif otype == 'autoscaling':
        asg_tag = {
            'ResourceId': name,
            'ResourceType': 'auto-scaling-group',
            'PropagateAtLaunch': True
            }
        new_tag[0] = new_tag[0] + asg_tag
        conn.create_or_update_tags(Tags=new_tag)
    # S3
    elif otype == 's3':
        response = conn.get_bucket_tagging(Bucket=name)
        if check_response(response):
            tags = response['TagSet']
            tags.expend(new_tag)
            conn.put_bucket_tagging(Bucket=name, Tagging={'TagSet': tags})
    # RDS
    elif otype == 'rds':
        arn = create_arn(otype, region, name)
        conn.add_tags_to_resource(ResourceName=arn, Tags=new_tag)
    # EMR
    elif otype == 'emr':
        conn.add_tags(Resources=name, Tags=new_tag)
    # REDSHIFT
    elif otype == 'redshift':
        arn = create_arn(otype, region, name)
        conn.creat_tags(ResourceName=arn, Tags=new_tag)
    # ELASTICCACHE
    elif otype == 'elasticcache':
        arn = create_arn(otype, region, name)
        conn.add_tags_to_resource(ResourceName=arn, Tags=new_tag)
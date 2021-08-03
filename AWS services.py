'''
This script creates an EC2 instance from a custom AMI ID and keeps the instance alive for 3 minutes (can be modified as per needs).
Before creating the EC2 instance, it creates a VPC of CIDR Block - 10.0.0.0/16 & a subnet of 10.0.0.0/24 (Can be modified as per needs).
It also creates an Internet Gateway and a route table for the Gateway and required route to open the traffic for VPC. It also associates
the route table for Gateway with the created subnet. After terminating the created instances, it deallocates all the allocated resources
automatically. The script is crude in the sense, it assumes no exceptions and only serves the required functionalities. The parameters are
all hardcoded for easy use. It assumes AWS access credentials, AWS CLI configurations and all the required dependencies already present.
'''
import boto3
from time import sleep
ec2 = boto3.resource('ec2')
client = boto3.client('ec2')

#Create a VPC of CIDR Block 10.0.0.0/16
vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
#Create a Subnet of 10.0.0.0/24 within the VPC
subnet = vpc.create_subnet(CidrBlock='10.0.0.0/24')
gateway = ec2.create_internet_gateway() #Create Internet Gateway
gateway.attach_to_vpc(VpcId=vpc.vpc_id) #Attach the Gateway to VPC

vpcid = vpc.vpc_id
subnetid = subnet.subnet_id
gatewayid = gateway.internet_gateway_id

print "VPC Created : " + vpcid
print "Subnet Created : " + subnetid
print "Gateway Created and Attached to VPC. Gateway ID : " + gatewayid

#Create a Seperate Route Table for the Internet Gateway
response = client.create_route_table(VpcId=vpcid)
route_table_id = response['RouteTable']['RouteTableId']
print "Seperate Route Table created for Internet Gateway. ID : " + route_table_id

#Add Route Entry for the Internet Gateway and open the VPC for the world through Gateway
response = client.create_route(
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=gatewayid,
    RouteTableId=route_table_id,
)
if response['Return']:
    print "Route Created for Internet Gateway"

'''Associate the Subnet explicitly with the Route Table for Gateway to allow traffic
   from Gateway into the subnet'''
association_id = client.associate_route_table(
    RouteTableId=route_table_id,
    SubnetId=subnetid
)['AssociationId']
print "Route Table associated with Subnet."

#Create Security Group
response = client.create_security_group(
    Description='Automated Security Group for Automated EC2 instances',
    GroupName='Cloudpeak-Security-Group',
    VpcId=vpcid
)
sg_id = response['GroupId']
print "Security Group Created. Security Group is : " + sg_id

#Authorize ingress of SSH from anywhere into the Security Group
response = client.authorize_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[
        {
            'FromPort': 22,
            'IpProtocol': 'tcp',
            'IpRanges': [
                {
                    'CidrIp': '0.0.0.0/0',
                    'Description': 'SSH access from anywhere',
                },
            ],
            'ToPort': 22,
        },
    ],
)
print "Security Group Ingress added for SSH access from anywhere."

instance_id_list = []
instance_ip_addr = []
print "Bringing Up Instances"
# create a new EC2 instance. To increase the number of instances increase Max Count parameter
instances = ec2.create_instances(
     ImageId='<AMI_IMAGE_ID>',
     MinCount=1,
     MaxCount=1,
     InstanceType='t2.large',
     KeyName='<KEY_PAIR_NAME>',
     NetworkInterfaces=[{'AssociatePublicIpAddress': True,
                         'DeviceIndex' : 0,
                         'SubnetId' : subnetid,
                         'Groups' : [sg_id]
                         }]
 )

for instance in instances:
    instance_id_list.append(instance.instance_id)
print "Created Instance ID's : "
print instance_id_list

sleep(15)

for id in instance_id_list:
    instance_ip_addr.append(ec2.Instance(id).public_ip_address)

print "Public IP addresses of the created Instances : "
print instance_ip_addr

print "\nThe Instances will be running for next 3 minutes before they are terminated.\n"
sleep(180)

ec2.instances.filter(InstanceIds=instance_id_list).terminate() #Terminate the instances
print "Instances Terminated. Will wait for 1 minute before proceeding deletion of all created resources."
sleep(60)

#Delete Security Group
response = client.delete_security_group(
    GroupId=sg_id,
)
print "Security Group Deleted."

#Dissociate Route Table from Subnet and Delete Route Table for Gateway
client.disassociate_route_table(AssociationId=association_id)
print "Route Table Disassociated from Subnet."
sleep(10)
client.delete_route_table(RouteTableId=route_table_id)
print "Route Table Deleted."
#Detach internet Gateway from VPC and Delete it
gateway.detach_from_vpc(VpcId=vpc.id)
print "Internet Gateway Detached from VPC."
sleep(5)
client.delete_internet_gateway(InternetGatewayId=gatewayid)
print "Internet Gateway Deleted."
sleep(5)
#Delete Subnet and VPC
client.delete_subnet(SubnetId=subnetid)
print "Subnet Deleted."
sleep(5)
client.delete_vpc(VpcId=vpcid)
print "VPC Deleted. Operations completed."
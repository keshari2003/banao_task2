# setup_aws_infra.py
import boto3

# --- Configuration ---
LOCALSTACK_ENDPOINT = 'http://localhost:4566'
REGION = 'us-east-1'

# --- Boto3 Clients ---
ec2_client = boto3.client('ec2', region_name=REGION, endpoint_url=LOCALSTACK_ENDPOINT)
elb_client = boto3.client('elb', region_name=REGION, endpoint_url=LOCALSTACK_ENDPOINT)
ec2_resource = boto3.resource('ec2', region_name=REGION, endpoint_url=LOCALSTACK_ENDPOINT)

print("🔧 Starting infrastructure setup...")

# 1. Create VPC
print("Creating VPC...")
vpc_response = ec2_client.create_vpc(CidrBlock='10.0.0.0/16')
vpc_id = vpc_response['Vpc']['VpcId']
ec2_client.get_waiter('vpc_available').wait(VpcIds=[vpc_id])
ec2_client.create_tags(Resources=[vpc_id], Tags=[{'Key': 'Name', 'Value': 'my-local-vpc'}])
print(f"✅ VPC created with ID: {vpc_id}")

# 2. Create two Subnets
print("Creating Subnets...")
subnet1_response = ec2_client.create_subnet(VpcId=vpc_id, CidrBlock='10.0.1.0/24', AvailabilityZone=f"{REGION}a")
subnet1_id = subnet1_response['Subnet']['SubnetId']
ec2_client.create_tags(Resources=[subnet1_id], Tags=[{'Key': 'Name', 'Value': 'public-subnet-a'}])

subnet2_response = ec2_client.create_subnet(VpcId=vpc_id, CidrBlock='10.0.2.0/24', AvailabilityZone=f"{REGION}b")
subnet2_id = subnet2_response['Subnet']['SubnetId']
ec2_client.create_tags(Resources=[subnet2_id], Tags=[{'Key': 'Name', 'Value': 'public-subnet-b'}])
print(f"✅ Subnets created: {subnet1_id}, {subnet2_id}")

# 3. Create Internet Gateway and attach to VPC
print("Creating Internet Gateway...")
igw_response = ec2_client.create_internet_gateway()
igw_id = igw_response['InternetGateway']['InternetGatewayId']
ec2_client.attach_internet_gateway(VpcId=vpc_id, InternetGatewayId=igw_id)
print(f"✅ Internet Gateway created and attached: {igw_id}")

# 4. Create Route Table and Public Route
print("Creating Route Table...")
route_table_response = ec2_client.create_route_table(VpcId=vpc_id)
rt_id = route_table_response['RouteTable']['RouteTableId']
ec2_client.create_route(RouteTableId=rt_id, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw_id)
ec2_client.associate_route_table(SubnetId=subnet1_id, RouteTableId=rt_id)
ec2_client.associate_route_table(SubnetId=subnet2_id, RouteTableId=rt_id)
print(f"✅ Route Table created and associated: {rt_id}")

# 5. Create Security Group
print("Creating Security Group...")
sg_response = ec2_client.create_security_group(
    GroupName='WebServerSG', Description='Allow HTTP', VpcId=vpc_id
)
sg_id = sg_response['GroupId']
ec2_client.authorize_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[{'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}]
)
print(f"✅ Security Group created: {sg_id}")

# 6. Create EC2 Instances (dummy targets)
print("Launching EC2 instances...")
instance_response = ec2_resource.create_instances(
    ImageId='ami-0ff8a91507f77f867',
    InstanceType='t2.micro',
    MinCount=2,
    MaxCount=2,
    SecurityGroupIds=[sg_id],
    SubnetId=subnet1_id
)
instance_ids = [instance.id for instance in instance_response]
waiter = ec2_client.get_waiter('instance_running')
waiter.wait(InstanceIds=instance_ids)
print(f"✅ EC2 Instances launched: {', '.join(instance_ids)}")

# 7. Create Classic Load Balancer
print("Creating Classic Load Balancer...")
lb_name = 'my-classic-lb'
lb_response = elb_client.create_load_balancer(
    LoadBalancerName=lb_name,
    Listeners=[
        {
            'Protocol': 'HTTP',
            'LoadBalancerPort': 80,
            'InstanceProtocol': 'HTTP',
            'InstancePort': 80,
        },
    ],
    Subnets=[subnet1_id, subnet2_id],
    SecurityGroups=[sg_id]
)
print(f"✅ Classic Load Balancer created with DNS: {lb_response['DNSName']}")

# 8. Register EC2 instances with the Classic Load Balancer
print("Registering instances with Load Balancer...")
targets = [{'InstanceId': instance_id} for instance_id in instance_ids]
elb_client.register_instances_with_load_balancer(
    LoadBalancerName=lb_name,
    Instances=targets
)
print("✅ Instances registered.")

print("\n🎉 Infrastructure setup complete!")
import boto3

# --- Configuration ---
LOCALSTACK_ENDPOINT = 'http://localhost:4566'
REGION = 'us-east-1'

# --- Boto3 Clients ---
ec2_client = boto3.client('ec2', region_name=REGION, endpoint_url=LOCALSTACK_ENDPOINT)
elb_client = boto3.client('elb', region_name=REGION, endpoint_url=LOCALSTACK_ENDPOINT) # CHANGED

print(" Starting infrastructure verification...")
lb_name = 'my-classic-lb'

# Verify VPC
vpcs = ec2_client.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': ['my-local-vpc']}])
if vpcs['Vpcs']:
    vpc = vpcs['Vpcs'][0]
    print(f"\n--- VPC Details ---")
    print(f"  ID: {vpc['VpcId']}, State: {vpc['State']}, CIDR: {vpc['CidrBlock']}")
else:
    print("\n VPC not found.")

# Verify Subnets
subnets = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}])
print(f"\n--- Subnet Details ({len(subnets['Subnets'])} found) ---")
for subnet in subnets['Subnets']:
    print(f"  ID: {subnet['SubnetId']}, State: {subnet['State']}, CIDR: {subnet['CidrBlock']}")

# Verify EC2 Instances
instances = ec2_client.describe_instances(Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}])
instance_count = sum(len(res['Instances']) for res in instances['Reservations'])
print(f"\n--- EC2 Instance Details ({instance_count} found) ---")
for reservation in instances['Reservations']:
    for instance in reservation['Instances']:
        print(f"  ID: {instance['InstanceId']}, State: {instance['State']['Name']}, Type: {instance['InstanceType']}")

# --- MODIFIED SECTION ---
# Verify Classic Load Balancer and Health
try:
    lbs = elb_client.describe_load_balancers(LoadBalancerNames=[lb_name])
    if lbs['LoadBalancerDescriptions']:
        lb = lbs['LoadBalancerDescriptions'][0]
        print(f"\n--- Classic Load Balancer Details ---")
        print(f"  Name: {lb['LoadBalancerName']}, Scheme: {lb['Scheme']}")
        
        health = elb_client.describe_instance_health(LoadBalancerName=lb_name)
        print("  Instance Health:")
        for instance in health['InstanceStates']:
            print(f"    - ID: {instance['InstanceId']}, State: {instance['State']}")
    else:
        print("\n Classic Load Balancer not found.")
except elb_client.exceptions.AccessPointNotFoundException:
    print(f"\n Classic Load Balancer '{lb_name}' not found.")
# --- END MODIFIED SECTION ---

print("\n Verification complete.")

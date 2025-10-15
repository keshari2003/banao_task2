# # verify_infra.py
# import boto3

# # --- Configuration ---
# LOCALSTACK_ENDPOINT = 'http://localhost:4566'
# REGION = 'us-east-1'

# # --- Boto3 Clients ---
# ec2_client = boto3.client('ec2', region_name=REGION, endpoint_url=LOCALSTACK_ENDPOINT)
# elbv2_client = boto3.client('elbv2', region_name=REGION, endpoint_url=LOCALSTACK_ENDPOINT)

# print("🔍 Starting infrastructure verification...")

# # Verify VPC
# vpcs = ec2_client.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': ['my-local-vpc']}])
# if vpcs['Vpcs']:
#     vpc = vpcs['Vpcs'][0]
#     print(f"\n--- VPC Details ---")
#     print(f"  ID: {vpc['VpcId']}, State: {vpc['State']}, CIDR: {vpc['CidrBlock']}")
# else:
#     print("\n❌ VPC not found.")

# # Verify Subnets
# subnets = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}])
# print(f"\n--- Subnet Details ({len(subnets['Subnets'])} found) ---")
# for subnet in subnets['Subnets']:
#     print(f"  ID: {subnet['SubnetId']}, State: {subnet['State']}, CIDR: {subnet['CidrBlock']}")

# # Verify EC2 Instances
# instances = ec2_client.describe_instances(Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}])
# instance_count = sum(len(res['Instances']) for res in instances['Reservations'])
# print(f"\n--- EC2 Instance Details ({instance_count} found) ---")
# for reservation in instances['Reservations']:
#     for instance in reservation['Instances']:
#         print(f"  ID: {instance['InstanceId']}, State: {instance['State']['Name']}, Type: {instance['InstanceType']}")

# # Verify Load Balancer
# lbs = elbv2_client.describe_load_balancers(Names=['my-app-lb'])
# if lbs['LoadBalancers']:
#     lb = lbs['LoadBalancers'][0]
#     print(f"\n--- Load Balancer Details ---")
#     print(f"  Name: {lb['LoadBalancerName']}, State: {lb['State']['Code']}, Scheme: {lb['Scheme']}")
# else:
#     print("\n❌ Load Balancer not found.")

# # Verify Target Group and Health
# tgs = elbv2_client.describe_target_groups(Names=['my-app-targets'])
# if tgs['TargetGroups']:
#     tg_arn = tgs['TargetGroups'][0]['TargetGroupArn']
#     print(f"\n--- Target Group Details ---")
#     print(f"  Name: {tgs['TargetGroups'][0]['TargetGroupName']}, Protocol: {tgs['TargetGroups'][0]['Protocol']}")
    
#     health = elbv2_client.describe_target_health(TargetGroupArn=tg_arn)
#     print("  Target Health:")
#     for target in health['TargetHealthDescriptions']:
#         print(f"    - ID: {target['Target']['Id']}, State: {target['TargetHealth']['State']}")
# else:
#     print("\n❌ Target Group not found.")

# print("\n✅ Verification complete.")

#------------------------------------------------------------------------




# verify_infra.py
import boto3

# --- Configuration ---
LOCALSTACK_ENDPOINT = 'http://localhost:4566'
REGION = 'us-east-1'

# --- Boto3 Clients ---
ec2_client = boto3.client('ec2', region_name=REGION, endpoint_url=LOCALSTACK_ENDPOINT)
elb_client = boto3.client('elb', region_name=REGION, endpoint_url=LOCALSTACK_ENDPOINT) # CHANGED

print("🔍 Starting infrastructure verification...")
lb_name = 'my-classic-lb'

# Verify VPC
vpcs = ec2_client.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': ['my-local-vpc']}])
if vpcs['Vpcs']:
    vpc = vpcs['Vpcs'][0]
    print(f"\n--- VPC Details ---")
    print(f"  ID: {vpc['VpcId']}, State: {vpc['State']}, CIDR: {vpc['CidrBlock']}")
else:
    print("\n❌ VPC not found.")

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
        print("\n❌ Classic Load Balancer not found.")
except elb_client.exceptions.AccessPointNotFoundException:
    print(f"\n❌ Classic Load Balancer '{lb_name}' not found.")
# --- END MODIFIED SECTION ---

print("\n✅ Verification complete.")
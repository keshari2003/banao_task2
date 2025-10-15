import boto3

# --- Configuration ---
LOCALSTACK_ENDPOINT = 'http://localhost:4566'
REGION = 'us-east-1'

# --- Boto3 Clients ---
ec2_client = boto3.client('ec2', region_name=REGION, endpoint_url=LOCALSTACK_ENDPOINT)
elb_client = boto3.client('elb', region_name=REGION, endpoint_url=LOCALSTACK_ENDPOINT) # CHANGED

print(" Starting infrastructure cleanup...")

try:
    # --- Clean up ELB resources ---
    lb_name = 'my-classic-lb'
    print(f"Deleting Classic Load Balancer '{lb_name}'...")
    elb_client.delete_load_balancer(LoadBalancerName=lb_name)
    print("Load Balancer deleted.")

    # --- Clean up EC2 and VPC resources ---
    vpc = ec2_client.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': ['my-local-vpc']}])['Vpcs'][0]
    vpc_id = vpc['VpcId']

    print(f"Finding resources in VPC {vpc_id}...")
    
    # Terminate Instances
    instances = ec2_client.describe_instances(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    instance_ids = [inst['InstanceId'] for res in instances['Reservations'] for inst in res['Instances']]
    if instance_ids:
        print(f"Terminating instances: {instance_ids}...")
        ec2_client.terminate_instances(InstanceIds=instance_ids)
        waiter = ec2_client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=instance_ids)
        print("Instances terminated.")

    # Delete Security Groups
    sgs = ec2_client.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    for sg in sgs['SecurityGroups']:
        if sg['GroupName'] != 'default':
            print(f"Deleting Security Group {sg['GroupId']}...")
            ec2_client.delete_security_group(GroupId=sg['GroupId'])

    # Detach and Delete Internet Gateway
    igws = ec2_client.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])
    for igw in igws['InternetGateways']:
        print(f"Detaching and deleting IGW {igw['InternetGatewayId']}...")
        ec2_client.detach_internet_gateway(VpcId=vpc_id, InternetGatewayId=igw['InternetGatewayId'])
        ec2_client.delete_internet_gateway(InternetGatewayId=igw['InternetGatewayId'])
        
    # Delete Route Tables (non-main)
    rts = ec2_client.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    for rt in rts['RouteTables']:
        is_main = any(assoc.get('Main', False) for assoc in rt['Associations'])
        if not is_main:
            for assoc in rt['Associations']:
                 ec2_client.disassociate_route_table(AssociationId=assoc['RouteTableAssociationId'])
            print(f"Deleting Route Table {rt['RouteTableId']}...")
            ec2_client.delete_route_table(RouteTableId=rt['RouteTableId'])
    
    # Delete Subnets
    subnets = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    for subnet in subnets['Subnets']:
        print(f"Deleting Subnet {subnet['SubnetId']}...")
        ec2_client.delete_subnet(SubnetId=subnet['SubnetId'])

    # Finally, delete the VPC
    print(f"Deleting VPC {vpc_id}...")
    ec2_client.delete_vpc(VpcId=vpc_id)

    print("\n Cleanup complete!")

except Exception as e:
    print(f"\n An error occurred during cleanup: {e}")
    print("Some resources might not have been created or were already deleted.")

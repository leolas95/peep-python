from aws_cdk import (CfnOutput, Stack, aws_ec2 as ec2)
from constructs import Construct


class SubnetStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Use the default VPC
        vpc = ec2.Vpc.from_lookup(self, "DefaultVPC", is_default=True)

        # Create a new private subnet in the default VPC
        private_subnet_us_east_1a = ec2.CfnSubnet(
            self,
            "PrivateSubnetUS_EAST_1A",
            vpc_id=vpc.vpc_id,
            cidr_block="172.31.96.0/28",  # Adjust CIDR block to avoid conflicts with existing subnets
            availability_zone='us-east-1a',  # Specify an AZ (e.g., 'us-east-1a')
            map_public_ip_on_launch=False,  # Disable public IP assignment
        )

        private_subnet_us_east_1b = ec2.CfnSubnet(
            self,
            "PrivateSubnetUS_EAST_1B",
            vpc_id=vpc.vpc_id,
            cidr_block="172.31.97.0/28",  # Adjust CIDR block to avoid conflicts with existing subnets
            availability_zone='us-east-1b',  # Specify an AZ (e.g., 'us-east-1a')
            map_public_ip_on_launch=False,  # Disable public IP assignment
        )

        # Create a new route table for the private subnet
        private_route_table = ec2.CfnRouteTable(
            self,
            "PrivateRouteTable",
            vpc_id=vpc.vpc_id
        )

        # Associate the private subnet with the private route table
        ec2.CfnSubnetRouteTableAssociation(
            self,
            "PrivateSubnetRouteTableAssociationUS_EAST_1A",
            subnet_id=private_subnet_us_east_1a.ref,
            route_table_id=private_route_table.ref
        )

        ec2.CfnSubnetRouteTableAssociation(
            self,
            "PrivateSubnetRouteTableAssociationUS_EAST_1B",
            subnet_id=private_subnet_us_east_1b.ref,
            route_table_id=private_route_table.ref
        )

        CfnOutput(self, "VPCId", value=vpc.vpc_id)
        CfnOutput(self, "PrivateSubnetUsEast1aId", value=private_subnet_us_east_1a.ref,
                  description="The ID of the private subnet for the first AZ in the VPC",
                  export_name="PrivateSubnetUsEast1aId")
        CfnOutput(self, "PrivateSubnetUsEast1bId", value=private_subnet_us_east_1b.ref,
                  description="The ID of the private subnet for the second AZ in the VPC",
                  export_name="PrivateSubnetUsEast1bId")

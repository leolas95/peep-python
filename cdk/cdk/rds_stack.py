import os.path

from aws_cdk import (CfnOutput, Duration, Fn, SecretValue, Stack, aws_ec2 as ec2, aws_rds as rds)
from constructs import Construct
from dotenv import load_dotenv

dirname = os.path.dirname(__file__)

load_dotenv(dotenv_path='../../.env')


class RdsInstanceStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Lookup default VPC
        vpc = ec2.Vpc.from_lookup(self, "DefaultVPC", is_default=True)

        # Import the private subnets ID from Stack 1
        private_subnet_id_us_east_1a = Fn.import_value("PrivateSubnetUsEast1aId")
        private_subnet_id_us_east_1b = Fn.import_value("PrivateSubnetUsEast1bId")

        # Use the imported subnet ID to create a reference to the existing subnet
        private_subnet_us_east_1a = ec2.Subnet.from_subnet_id(self, "ImportedPrivateSubnetUsEast1a",
                                                              private_subnet_id_us_east_1a)
        private_subnet_us_east_1b = ec2.Subnet.from_subnet_id(self, "ImportedPrivateSubnetUsEast1b",
                                                              private_subnet_id_us_east_1b)

        rds_sg = ec2.SecurityGroup(
            self, "RdsSecurityGroup",
            vpc=vpc,
            description="Allow Lambda access to RDS",
            allow_all_outbound=True
        )

        # Create the PostgreSQL RDS instance
        db_instance = rds.DatabaseInstance(
            self,
            "PostgresInstance",
            database_name="PeepDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16
            ),
            vpc=vpc,
            credentials=rds.Credentials.from_password(
                username=os.getenv('DB_USER'),
                password=SecretValue.unsafe_plain_text(os.getenv('DB_PASSWORD'))
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T4G, ec2.InstanceSize.MICRO
            ),
            storage_type=rds.StorageType.GP2,  # General Purpose SSD (free-tier eligible)
            allocated_storage=20,  # Free-tier limit: 20 GB
            max_allocated_storage=20,  # Prevent automatic scaling beyond free-tier limits
            deletion_protection=False,  # Disable deletion protection to allow easy stack deletion
            publicly_accessible=True,
            backup_retention=Duration.days(1),  # Short retention period to stay within free-tier limits
            vpc_subnets=ec2.SubnetSelection(subnets=[private_subnet_us_east_1a, private_subnet_us_east_1b]),
            availability_zone='us-east-1a',
            security_groups=[rds_sg],
        )

        # TODO: fix issue db peep_python doesnt exist. At least they are connected now.

        CfnOutput(self, "RDSInstanceIdentifier", value=db_instance.instance_identifier,
                  export_name="RDSInstanceIdentifier")
        CfnOutput(self, "RDSInstanceEndpoint", value=db_instance.db_instance_endpoint_address,
                  export_name="RDSInstanceEndpoint",
                  description="The endpoint of the RDS instance")

        CfnOutput(self, "RDSInstanceSecurityGroup", value=db_instance.connections.security_groups[0].security_group_id,
                  export_name="RDSInstanceSecurityGroup",
                  description="The ID of the instance security group")

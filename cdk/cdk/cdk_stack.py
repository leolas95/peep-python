import os.path

from aws_cdk import (
    CfnOutput,
    Duration,
    Fn,
    Stack,
    aws_apigateway as apigw,
    aws_ec2 as ec2,
    aws_lambda as lambda_,
    aws_ssm as ssm,
)
from constructs import Construct
from dotenv import load_dotenv

dirname = os.path.dirname(__file__)

load_dotenv(dotenv_path='../.env')


# class PeepStack(Stack):
#     def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
#         super().__init__(scope, construct_id, **kwargs)
#
#         vpc = ec2.Vpc(self, 'PeepVPC')
#         ami_id = 'ami-0e2c8caa4b6378d8c'  # Ubuntu noble 24.04 amd64 (x86-64): https://us-east-1.console.aws.amazon.com/ec2/home?region=us-east-1#ImageDetails:imageId=ami-0e2c8caa4b6378d8c
#         machine_image = ec2.MachineImage.generic_linux({
#             "us-east-1": ami_id
#         })
#         instance = ec2.Instance(self, 'PeepInstance', vpc=vpc,
#                                 machine_image=machine_image,
#                                 instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MICRO),
#                                 vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
#                                 associate_public_ip_address=True
#                                 )
#
#         # Script in S3 as Asset
#         configure_asset = Asset(self, "Asset", path=os.path.join(dirname, "configure.sh"))
#         local_path = instance.user_data.add_s3_download_command(
#             bucket=configure_asset.bucket,
#             bucket_key=configure_asset.s3_object_key
#         )
#
#         # Userdata executes script from S3
#         instance.user_data.add_execute_file_command(
#             file_path=local_path
#         )
#         configure_asset.grant_read(instance.role)
#
#         # Allow inbound traffic to the instance
#         sg = instance.connections.security_groups[0]
#         sg.add_ingress_rule(
#             peer=ec2.Peer.any_ipv4(),
#             connection=ec2.Port.tcp(22)  # SSH
#         )
#         sg.add_ingress_rule(
#             peer=ec2.Peer.any_ipv4(),
#             connection=ec2.Port.tcp(80)  # HTTP
#         )
#         sg.add_ingress_rule(
#             peer=ec2.Peer.any_ipv4(),
#             connection=ec2.Port.tcp(443)  # HTTPS
#         )

class PeepStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Use the default VPC
        vpc = ec2.Vpc.from_lookup(self, "DefaultVPC", is_default=True)

        # Create a new private subnet in the default VPC
        private_subnet_id_us_east_1a = Fn.import_value("PrivateSubnetUsEast1aId")

        # Use the imported subnet ID to create a reference to the existing subnet
        private_subnet_us_east_1a = ec2.Subnet.from_subnet_id(self, "ImportedPrivateSubnetUsEast1a",
                                                              private_subnet_id_us_east_1a)

        # Value is in the outputs when deploying the RdsInstanceStack
        rds_instance_endpoint = Fn.import_value("RDSInstanceEndpoint")

        lambda_sg = ec2.SecurityGroup(
            self,
            'LambdaSecurityGroup',
            vpc=vpc,
            description='Security Group for Lambda',
            allow_all_outbound=True
        )

        proxy_lambda_kwargs = {
            'runtime': lambda_.Runtime.PYTHON_3_10,
            'code': lambda_.Code.from_asset('../outputs/deployment_package.zip'),
            'handler': 'lambdas.main.handler',
            'architecture': lambda_.Architecture.ARM_64,
            'environment': {
                'PEEP_ENV': os.getenv('PEEP_ENV'),
                'DB_HOST': rds_instance_endpoint,
                'DB_PORT': os.getenv('DB_PORT'),
                'DB_NAME': os.getenv('DB_NAME')
            },
            'vpc': vpc,
            'vpc_subnets': ec2.SubnetSelection(subnets=[private_subnet_us_east_1a]),
            'security_groups': [lambda_sg],
            'timeout': Duration.seconds(30),
            'logging_format': lambda_.LoggingFormat.JSON,
        }
        proxy_lambda = lambda_.Function(self, 'ProxyLambda', **proxy_lambda_kwargs)
        proxy_lambda.node.add_dependency(private_subnet_us_east_1a)

        db_user = ssm.StringParameter.from_string_parameter_name(self, 'DBUser', '/peep/live/db-user')
        db_user.grant_read(proxy_lambda)
        db_password = ssm.StringParameter.from_string_parameter_name(self, 'DBPassword',
                                                                     '/peep/live/db-password')
        db_password.grant_read(proxy_lambda)

        # Import the RDS instance
        rds_sg_id = Fn.import_value("RDSInstanceSecurityGroup")
        rds_sg = ec2.SecurityGroup.from_security_group_id(self, "ImportedRDSInstanceSG", rds_sg_id)
        rds_sg.add_ingress_rule(
            peer=lambda_sg,
            connection=ec2.Port.tcp(int(os.getenv('DB_PORT'))),
            description='Allow Lambda to read and write from RDS'
        )

        api = apigw.LambdaRestApi(self, 'PeepAPI', handler=proxy_lambda)

        # Outputs
        CfnOutput(self, 'APIGateway URL', value=api.url)
        CfnOutput(self, 'ProxyLambdaArn', value=proxy_lambda.function_arn)
        CfnOutput(self, 'ProxyLambdaFunctionName', value=proxy_lambda.function_name)

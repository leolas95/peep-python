#!/usr/bin/env python3

import aws_cdk as cdk

from cdk.cdk_stack import PeepStack
from cdk.rds_stack import RdsInstanceStack
from cdk.subnet_stack import SubnetStack

app = cdk.App()
SubnetStack(app, "SubnetStack", env=cdk.Environment(account='949635788109', region='us-east-1'))
RdsInstanceStack(app, "RdsInstanceStack", env=cdk.Environment(account='949635788109', region='us-east-1'))
PeepStack(app, "PeepStack",
          # If you don't specify 'env', this stack will be environment-agnostic.
          # Account/Region-dependent features and context lookups will not work,
          # but a single synthesized template can be deployed anywhere.

          # Uncomment the next line to specialize this stack for the AWS Account
          # and Region that are implied by the current CLI configuration.

          # env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

          # Uncomment the next line if you know exactly what Account and Region you
          # want to deploy the stack to. */

          env=cdk.Environment(account='949635788109', region='us-east-1'),

          # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
          )

app.synth()

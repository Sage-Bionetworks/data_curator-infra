import config

from aws_cdk import (Stack,
    aws_ec2 as ec2,
    Tags)

from constructs import Construct

VPC_CIDR_CONTEXT= "VPC_CIDR"

class VpcStack(Stack):

    def __init__(self, scope: Construct, context: str, env: dict, **kwargs) -> None:
        stack_id = f'{env.get(config.STACK_NAME_PREFIX_CONTEXT)}-common'
        super().__init__(scope, stack_id, **kwargs)
        self.vpc = ec2.Vpc(self,
                           f'{stack_id}-vpc',
                           cidr=env.get(VPC_CIDR_CONTEXT),
                           max_azs=2)

        # Tag all resources in this Stack's scope with context tags
        for key, value in env.get(config.TAGS_CONTEXT).items():
            Tags.of(scope).add(key, value)

#!/usr/bin/env python3
import aws_cdk as cdk

from src.common.vpc_stack import VpcStack
from src.docker_fargate.docker_fargate_stack import DockerFargateStack

app = cdk.App()
vpc_stack = VpcStack(app)
docker_fargate_stack = DockerFargateStack(app, vpc=vpc_stack.vpc)
docker_fargate_stack.add_dependency(vpc_stack)

app.synth()

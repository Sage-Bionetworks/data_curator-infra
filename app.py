#!/usr/bin/env python3
import aws_cdk as cdk

from common.vpc_stack import VpcStack
from docker_fargate.docker_fargate_stack import DockerFargateStack

app = cdk.App()

env = app.node.try_get_context('env')
app_config = app.node.try_get_context(env)

vpc_stack = VpcStack(app, app_config)
docker_fargate_stack = DockerFargateStack(app, app_config, vpc=vpc_stack.vpc)
docker_fargate_stack.add_dependency(vpc_stack)

app.synth()

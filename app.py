#!/usr/bin/env python3
import aws_cdk as cdk
import helpers

from common.vpc_stack import VpcStack
from docker_fargate.docker_fargate_stack import DockerFargateStack

app = cdk.App()
try:
  context, app_config = helpers.get_app_config(app)
except Exception as err:
  raise SystemExit(err)

vpc_stack = VpcStack(app, context, app_config)
docker_fargate_stack = DockerFargateStack(app, context, app_config, vpc=vpc_stack.vpc)
docker_fargate_stack.add_dependency(vpc_stack)

app.synth()

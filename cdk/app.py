#!/usr/bin/env python3
import os

import aws_cdk as cdk

from docker_fargate.docker_fargate_stack import DockerFargateStack


app = cdk.App()
DockerFargateStack(app)

app.synth()

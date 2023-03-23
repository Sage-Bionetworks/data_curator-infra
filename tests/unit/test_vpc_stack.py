import aws_cdk as core
import aws_cdk.assertions as assertions
import config

from common.vpc_stack import VpcStack

def test_vpc_created():
    app = core.App()
    app_config = {config.TAGS_CONTEXT: {"TagName": "TagValue"}}

    stack = VpcStack(app, "dev", app_config)
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::EC2::VPC", {
        "EnableDnsHostnames": True
    })

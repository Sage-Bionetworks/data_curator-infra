import aws_cdk as core
import aws_cdk.assertions as assertions

from src.common.vpc_stack import VpcStack

def test_vpc_created():
    app = core.App()
    stack = VpcStack(app)
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::EC2::VPC", {
        "EnableDnsHostnames": True
    })

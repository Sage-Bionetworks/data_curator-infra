
from aws_cdk import (Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ssm as ssm,
    aws_elasticloadbalancingv2 as elbv2,
    aws_route53 as r53,
    Duration,
    Tags)

import config as config
import aws_cdk.aws_secretsmanager as sm
from constructs import Construct

ID_SUFFIX = "-DockerFargateStack"
CLUSTER_SUFFIX = "-Cluster"
SERVICE_SUFFIX = "-Service"

IMAGE_PATH_AND_TAG_CONTEXT = "IMAGE_PATH_AND_TAG"
STACK_NAME_PREFIX_CONTEXT = "STACK_NAME_PREFIX"
PORT_NUMBER_CONTEXT = "PORT"
HOST_NAME_CONTEXT = "HOST_NAME"
HOSTED_ZONE_NAME_CONTEXT = "HOSTED_ZONE_NAME"
HOSTED_ZONE_ID_CONTEXT = "HOSTED_ZONE_ID"
VPC_CIDR_CONTEXT = "VPC_CIDR"

# The name of the environment variable that will hold the secrets
SECRETS_MANAGER_ENV_NAME = "SECRETS_MANAGER_SECRETS"
CONTAINER_ENV = "CONTAINER_ENV" # name of env passed from GitHub action
ENV_NAME = "ENV"

def create_id(env: dict) -> str:
    return env.get(STACK_NAME_PREFIX_CONTEXT) + ID_SUFFIX

def create_secret(scope: Construct, name: str) -> str:
    isecret = sm.Secret.from_secret_name_v2(scope, name, name)
    return ecs.Secret.from_secrets_manager(isecret)
    # see also: https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_ecs/Secret.html
    # see also: ecs.Secret.from_ssm_parameter(ssm.IParameter(parameter_name=name))

def get_container_env(env: dict) -> str:
    return env.get(CONTAINER_ENV)

def get_hosted_zone_name(env: dict) -> str:
    return env.get(HOSTED_ZONE_NAME_CONTEXT)

def get_hosted_zone_id(env: dict) -> str:
    return env.get(HOSTED_ZONE_ID_CONTEXT)

def get_vpc_cidr(env: dict) -> str:
    return env.get(VPC_CIDR_CONTEXT)

def get_host_name(env: dict) -> str:
    return env.get(HOST_NAME_CONTEXT)

def get_cluster_name(env: dict) -> str:
    return env.get(STACK_NAME_PREFIX_CONTEXT) + CLUSTER_SUFFIX

def get_service_name(env: dict) -> str:
    return env.get(STACK_NAME_PREFIX_CONTEXT) + SERVICE_SUFFIX

def get_secret_name(env: dict) -> str:
    return env.get(STACK_NAME_PREFIX_CONTEXT)

def get_docker_image_name(env: dict):
    return env.get(IMAGE_PATH_AND_TAG_CONTEXT)

def get_port(env: dict) -> int:
    return int(env.get(PORT_NUMBER_CONTEXT))


class DockerFargateStack(Stack):

    def __init__(self, scope: Construct, env: dict, vpc: ec2.Vpc, **kwargs) -> None:
        stack_id = create_id(env)
        super().__init__(scope, stack_id, **kwargs)

        cluster = ecs.Cluster(self, get_cluster_name(env), vpc=vpc, container_insights=True)

        secrets = {
            SECRETS_MANAGER_ENV_NAME: create_secret(self, get_secret_name(env))
        }

        env_vars = {}
        container_env = get_container_env(env)
        if container_env is not None:
            env_vars[ENV_NAME]=container_env

        task_image_options = ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                   image=ecs.ContainerImage.from_registry(get_docker_image_name(env)),
                   environment=env_vars,
                   secrets = secrets,
                   container_port = get_port(env))

        zone = r53.PublicHostedZone.from_public_hosted_zone_attributes(
            self,
            id=stack_id+"_zone",
            hosted_zone_id=get_hosted_zone_id(env),
            zone_name=get_hosted_zone_name(env))


        #
        # for options to pass to ApplicationLoadBalancedTaskImageOptions see:
        # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_ecs_patterns/ApplicationLoadBalancedTaskImageOptions.html#aws_cdk.aws_ecs_patterns.ApplicationLoadBalancedTaskImageOptions
        #
        load_balanced_fargate_service = ecs_patterns.\
                ApplicationLoadBalancedFargateService(self, get_service_name(env),
            cluster=cluster,            # Required
            cpu=256,                    # Default is 256
            desired_count=1,            # Number of copies of the 'task' (i.e. the app') running behind the ALB
            task_image_options=task_image_options,
            memory_limit_mib=1024,      # Default is 512
            public_load_balancer=True,  # Default is False
            # TLS:
            protocol=elbv2.ApplicationProtocol.HTTPS,
            ssl_policy=elbv2.SslPolicy.FORWARD_SECRECY_TLS12_RES, # Strong forward secrecy ciphers and TLS1.2 only.
            domain_name=get_host_name(env), # The domain name for the service, e.g. “api.example.com.”
            domain_zone=zone) #  The Route53 hosted zone for the domain, e.g. “example.com.”

        # Overriding health check timeout helps with sluggishly responding app's (e.g. Shiny)
        # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_elasticloadbalancingv2/ApplicationTargetGroup.html#aws_cdk.aws_elasticloadbalancingv2.ApplicationTargetGroup
        load_balanced_fargate_service.target_group.configure_health_check(interval=Duration.seconds(120), timeout=Duration.seconds(60))

        if False: # enable/disable autoscaling
            scalable_target = load_balanced_fargate_service.service.auto_scale_task_count(
               min_capacity=1, # Minimum capacity to scale to. Default: 1
               max_capacity=4 # Maximum capacity to scale to.
            )

            # Add more capacity when CPU utilization reaches 50%
            scalable_target.scale_on_cpu_utilization("CpuScaling",
                target_utilization_percent=50
            )

            # Add more capacity when memory utilization reaches 50%
            scalable_target.scale_on_memory_utilization("MemoryScaling",
                target_utilization_percent=50
            )

            # Other metrics to drive scaling are discussed here:
            # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_autoscaling/README.html

        # Tag all resources in this Stack's scope with a cost center tag
        Tags.of(scope).add(config.COST_CENTER_CONTEXT, env.get(config.COST_CENTER_CONTEXT))


from aws_cdk import (Stack,
	aws_ec2 as ec2, 
	aws_ecs as ecs,
	aws_ecs_patterns as ecs_patterns,
	aws_ssm as ssm,
	aws_elasticloadbalancingv2 as elbv2,
	aws_route53 as r53,
	Duration,
	Tags)

import os
import aws_cdk.aws_secretsmanager as sm
from constructs import Construct

STACK_NAME_PREFIX = "STACK_NAME_PREFIX"
ID_SUFFIX = "-DockerFargateStack"
VPC_SUFFIX = "-FargateVPC"
CLUSTER_SUFFIX = "-Cluster"
SERVICE_SUFFIX = "-Service"
DOCKER_IMAGE_NAME = "DOCKER_IMAGE"
COST_CENTER = "COST_CENTER"
COST_CENTER_TAG_NAME = "CostCenter"
PORT_NUMBER = "PORT"
HOST_NAME = "HOST_NAME"
HOSTED_ZONE_NAME = "HOSTED_ZONE_NAME"
HOSTED_ZONE_ID = "HOSTED_ZONE_ID"

# The name of the environment variable that will hold the secrets
SECRETS_MANAGER_ENV_NAME = "SECRETS_MANAGER_SECRETS"

def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or len(value)==0:
        raise Exception(f'{name} is required.')
    return value

def create_id() -> str:
    return get_required_env(STACK_NAME_PREFIX)+ID_SUFFIX


CONTAINER_ENV = "R_CONFIG_ACTIVE" # name of env passed from GitHub action
ENV_NAME = "R_CONFIG_ACTIVE"

def get_vpc_name() -> str:
    return get_required_env(STACK_NAME_PREFIX)+VPC_SUFFIX

def get_cluster_name() -> str:
    return get_required_env(STACK_NAME_PREFIX)+CLUSTER_SUFFIX

def get_service_name() -> str:
    return get_required_env(STACK_NAME_PREFIX)+SERVICE_SUFFIX

def get_secret_name() -> str:
    return get_required_env(STACK_NAME_PREFIX)

def get_docker_image_name():
    return get_required_env(DOCKER_IMAGE_NAME)

def get_cost_center() -> str:
    return get_required_env(COST_CENTER)

def get_port() -> int:
    return int(get_required_env(PORT_NUMBER))

def get_container_env() -> str:
    return os.getenv(CONTAINER_ENV)

def create_secret(scope: Construct, name: str) -> str:
    isecret = sm.Secret.from_secret_name_v2(scope, name, name)
    return ecs.Secret.from_secrets_manager(isecret)
    # see also: https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_ecs/Secret.html
    # see also: ecs.Secret.from_ssm_parameter(ssm.IParameter(parameter_name=name))

def get_hosted_zone_name() -> str:
	return os.getenv(HOSTED_ZONE_NAME)
	
def get_hosted_zone_id() -> str:
	return os.getenv(HOSTED_ZONE_ID)
	
def get_host_name() -> str:
	return os.getenv(HOST_NAME)

class DockerFargateStack(Stack):

    def __init__(self, scope: Construct, **kwargs) -> None:
        stack_id = create_id()
        super().__init__(scope, stack_id, **kwargs)

        vpc = ec2.Vpc(self, get_vpc_name(), max_azs=2)

        cluster = ecs.Cluster(self, get_cluster_name(), vpc=vpc, container_insights=True)

        secrets = {
        	SECRETS_MANAGER_ENV_NAME: create_secret(self, get_secret_name())
        }

        env_vars = {}
        container_env = get_container_env()
        if container_env is not None:
            env_vars[ENV_NAME]=container_env

        task_image_options = ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
    	    	   image=ecs.ContainerImage.from_registry(get_docker_image_name()),
    	    	   environment=env_vars,
    	    	   secrets = secrets,
    	    	   container_port = get_port())
        
        zone = r53.PublicHostedZone.from_public_hosted_zone_attributes(self, id=stack_id+"_zone", hosted_zone_id=get_hosted_zone_id(), zone_name=get_hosted_zone_name())

 
        #
        # for options to pass to ApplicationLoadBalancedTaskImageOptions see:
        # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_ecs_patterns/ApplicationLoadBalancedTaskImageOptions.html#aws_cdk.aws_ecs_patterns.ApplicationLoadBalancedTaskImageOptions
        #
        load_balanced_fargate_service = ecs_patterns.\
                ApplicationLoadBalancedFargateService(self, get_service_name(),
            cluster=cluster,            # Required
            cpu=256,                    # Default is 256
            desired_count=1,            # Number of copies of the 'task' (i.e. the app') running behind the ALB
            task_image_options=task_image_options,
            memory_limit_mib=1024,      # Default is 512
            public_load_balancer=True,  # Default is False
            # TLS:
            protocol=elbv2.ApplicationProtocol.HTTPS,
            domain_name=get_host_name(), # The domain name for the service, e.g. “api.example.com.”
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

        Tags.of(load_balanced_fargate_service).add(COST_CENTER_TAG_NAME, get_cost_center())

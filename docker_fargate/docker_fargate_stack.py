from aws_cdk import (Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elbv2,
    aws_route53 as r53,
    aws_cloudwatch as cloudwatch,
    aws_applicationautoscaling as autoscaling,
    CfnOutput,
    Duration,
    Tags)

import config as config
import aws_cdk.aws_certificatemanager as cm
import aws_cdk.aws_secretsmanager as sm
from constructs import Construct

ACM_CERT_ARN_CONTEXT = "ACM_CERT_ARN"
IMAGE_PATH_AND_TAG_CONTEXT = "IMAGE_PATH_AND_TAG"
PORT_NUMBER_CONTEXT = "PORT"
STICKY = "STICKY"
DESIRED_TASK_COUNT="DESIRED_TASK_COUNT"
MIN_INSTANCE_COUNT="MIN_INSTANCE_COUNT"
MAX_INSTANCE_COUNT="MAX_INSTANCE_COUNT"
CPU_SIZE="CPU_SIZE"
MEMORY_SIZE="MEMORY_SIZE"

# The name of the environment variable that will hold the secrets
SECRETS_MANAGER_ENV_NAME = "SECRETS_MANAGER_SECRETS"
CONTAINER_ENV = "CONTAINER_ENV" # name of env passed from GitHub action
ENV_NAME = "ENV"

def get_secret(scope: Construct, id: str, name: str) -> str:
    isecret = sm.Secret.from_secret_name_v2(scope, id, name)
    return ecs.Secret.from_secrets_manager(isecret)
    # see also: https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_ecs/Secret.html
    # see also: ecs.Secret.from_ssm_parameter(ssm.IParameter(parameter_name=name))

def get_container_env(env: dict) -> str:
    return env.get(CONTAINER_ENV)

def get_certificate_arn(env: dict) -> str:
    return env.get(ACM_CERT_ARN_CONTEXT)

def get_docker_image_name(env: dict):
    return env.get(IMAGE_PATH_AND_TAG_CONTEXT)

def get_port(env: dict) -> int:
    return int(env.get(PORT_NUMBER_CONTEXT))

def get_desired_task_count(env: dict) -> int:
    return int(env.get(DESIRED_TASK_COUNT))

def get_sticky(env: dict) -> bool:
    return env.get(STICKY).lower()=="true"

def get_min_instance_count(env: dict) -> int:
    return int(env.get(MIN_INSTANCE_COUNT))

def get_max_instance_count(env: dict) -> int:
    return int(env.get(MAX_INSTANCE_COUNT))

def get_cpu_size(env: dict) -> int:
    return int(env.get(CPU_SIZE))

def get_memory_size(env: dict) -> int:
    return int(env.get(MEMORY_SIZE))

class DockerFargateStack(Stack):

    def __init__(self, scope: Construct, context: str, env: dict, vpc: ec2.Vpc, **kwargs) -> None:
        stack_prefix = f'{env.get(config.STACK_NAME_PREFIX_CONTEXT)}-{context}'
        stack_id = f'{stack_prefix}-DockerFargateStack'
        super().__init__(scope, stack_id, **kwargs)

        cluster = ecs.Cluster(
            self,
            f'{stack_prefix}-Cluster',
            vpc=vpc,
            container_insights=True)

        secret_name = f'{stack_id}/{context}/ecs'
        secrets = {
            SECRETS_MANAGER_ENV_NAME: get_secret(self, secret_name, secret_name)
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

        cert = cm.Certificate.from_certificate_arn(
            self,
            f'{stack_id}-Certificate',
            get_certificate_arn(env),
        )

        #
        # for options to pass to ApplicationLoadBalancedTaskImageOptions see:
        # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_ecs_patterns/ApplicationLoadBalancedTaskImageOptions.html#aws_cdk.aws_ecs_patterns.ApplicationLoadBalancedTaskImageOptions
        #
        load_balanced_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            f'{stack_prefix}-Service',
            cluster=cluster,            # Required
            cpu=get_cpu_size(env),                    # Default is 256
            desired_count=get_desired_task_count(env), # Number of copies of the 'task' (i.e. the app') running behind the ALB
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True), # Enable rollback on deployment failure
            task_image_options=task_image_options,
            memory_limit_mib=get_memory_size(env),      # Default is 512
            public_load_balancer=True,  # Default is False
            redirect_http=True,
            # TLS:
            certificate=cert,
            protocol=elbv2.ApplicationProtocol.HTTPS,
            ssl_policy=elbv2.SslPolicy.FORWARD_SECRECY_TLS12_RES, # Strong forward secrecy ciphers and TLS1.2 only.
        )

        # Overriding health check timeout helps with sluggishly responding app's (e.g. Shiny)
        # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_elasticloadbalancingv2/ApplicationTargetGroup.html#aws_cdk.aws_elasticloadbalancingv2.ApplicationTargetGroup
        load_balanced_fargate_service.target_group.configure_health_check(interval=Duration.seconds(120), timeout=Duration.seconds(60))
        if get_sticky(env):
            load_balanced_fargate_service.target_group.enable_cookie_stickiness(Duration.days(1), cookie_name=None)

        if True: # enable/disable autoscaling
            scalable_target = load_balanced_fargate_service.service.auto_scale_task_count(
               min_capacity=get_min_capacity_count(env), # Minimum capacity to scale to. Default: 1
               max_capacity=get_max_capacity_count(env) # Maximum capacity to scale to.
            )

            # Add more capacity when CPU utilization reaches 50%
            scalable_target.scale_on_cpu_utilization("CpuScaling",
                target_utilization_percent=70
            )

            # Add more capacity when memory utilization reaches 50%
            scalable_target.scale_on_memory_utilization("MemoryScaling",
                target_utilization_percent=70
            )

            # Other metrics to drive scaling are discussed here:
            # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_autoscaling/README.html
            # Add more capacity when active connections increase
            active_connection_metric = cloudwatch.Metric(
                namespace = "AWS/ApplicationELB",
                metric_name="ActiveConnectionCount",
                period=Duration.seconds(60),
                statistic="AVERAGE",
                dimensions_map={ "LoadBalancer": load_balanced_fargate_service.load_balancer.load_balancer_full_name }
            )

            scalable_target.scale_on_metric("ScaleToActiveConnection",
                metric=active_connection_metric,
                scaling_steps=[
                    autoscaling.ScalingInterval(lower=0, change=-1),
                    autoscaling.ScalingInterval(lower=3, change=+1),
                    autoscaling.ScalingInterval(lower=6, change=+2),
                    autoscaling.ScalingInterval(lower=9, change=+3)
                ],
                adjustment_type=autoscaling.AdjustmentType.CHANGE_IN_CAPACITY
            )

        # Tag all resources in this Stack's scope with context tags
        for key, value in env.get(config.TAGS_CONTEXT).items():
            Tags.of(scope).add(key, value)

        # Export load balancer name
        lb_dns_name = load_balanced_fargate_service.load_balancer.load_balancer_dns_name
        lb_dns_export_name = f'{stack_id}-LoadBalancerDNS'
        CfnOutput(self, 'LoadBalancerDNS', value=lb_dns_name, export_name=lb_dns_export_name)

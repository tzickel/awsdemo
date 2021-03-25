# Needed for a temporary hack
import time

from aws_cdk import (
    core as cdk,
    # aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_lambda_event_sources as lambda_event_sources,
    aws_iam as iam,
    custom_resources as cr,
)


# This function helps transform an S3 bucket PUT object event to environment variables input to the ECS task
lambda_function_code = """import boto3
import os

client = boto3.client("ecs")

capacityprovider = os.environ["CAPACITY_PROVIDER_NAME"]
cluster = os.environ["CLUSTER_NAME"]
containername = os.environ["CONTAINER_NAME"]
regionname = os.environ["REGION_NAME"]
outputbucketname = os.environ["OUTPUT_BUCKET_NAME"]
taskdefinition = os.environ["TASK_DEFINITION"]


def lambda_handler(event, context):
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    object_name = event["Records"][0]["s3"]["object"]["key"]
    task = client.run_task(
        capacityProviderStrategy=[
            {
                "capacityProvider": capacityprovider,
            },
        ],
        cluster=cluster,
        overrides={
            "containerOverrides": [
                {
                    "name": containername,
                    "environment": [
                        {"name": "REGION_NAME", "value": regionname},
                        {"name": "INPUT_BUCKET_NAME", "value": bucket_name},
                        {"name": "INPUT_OBJECT_NAME", "value": object_name},
                        {"name": "OUTPUT_BUCKET_NAME", "value": outputbucketname},
                    ],
                }
            ]
        },
        taskDefinition=taskdefinition,
    )
    return {
        "statusCode": 204,
    }
"""


# TODO would be nice if we can get rid of all names
class CdkDemoStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # TODO should this stuff be passed as inputs to the stack ?
        source_code_directory = "/opt/python"
        asg_parameters = {
            "instance_type": ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO
            ),
            "machine_image": ecs.EcsOptimizedImage.amazon_linux2(),
            "desired_capacity": 0,
            "max_capacity": 5,
            "min_capacity": 0,
        }
        container_settings = {
            "memory_limit_mib": 300,
            "logging": ecs.AwsLogDriver(stream_prefix="ecslogs"),
        }
        input_bucket_name = "cdkdemoinput"
        output_bucket_name = "cdkdemooutput"

        # Create an Docker image from an given directory, which will be later published to Amazon ECR
        # TODO can this be cleanup on destroy as well ?
        container_image = ecs.ContainerImage.from_asset(directory=source_code_directory)

        # Create an Amazon ECS cluster
        cluster = ecs.Cluster(self, "ecscluster")
        cluster.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

        # Create an auto scaling group for the ECS cluster
        asg = cluster.add_capacity("ecsautoscalinggroup", **asg_parameters)
        # TODO check if needed
        asg.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

        # Create a capacity provider for the ECS cluster based on the auto scaling group
        capacity_provider = ecs.CfnCapacityProvider(
            self,
            "ecscapacityprovider",
            # Name can't start with ecs...
            name="capacityproviderecs",
            auto_scaling_group_provider=ecs.CfnCapacityProvider.AutoScalingGroupProviderProperty(
                auto_scaling_group_arn=asg.auto_scaling_group_name,
                managed_scaling=ecs.CfnCapacityProvider.ManagedScalingProperty(
                    status="ENABLED"
                ),
                # TODO investigate this better
                managed_termination_protection="DISABLED",
            ),
        )
        capacity_provider.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

        # Currently the CDK checks if the string is FARGATE or FARGATE_SPOT and errors out
        # cluster.add_capacity_provider(capacity_provider.name)
        lame_hack = cr.AwsCustomResource(
            self,
            "lamehack",
            on_create={
                "service": "ECS",
                "action": "putClusterCapacityProviders",
                "parameters": {
                    "cluster": cluster.cluster_arn,
                    "capacityProviders": [capacity_provider.name],
                    "defaultCapacityProviderStrategy": [],
                },
                "physical_resource_id": cr.PhysicalResourceId.of(str(int(time.time()))),
            },
            on_delete={
                "service": "ECS",
                "action": "putClusterCapacityProviders",
                "parameters": {
                    "cluster": cluster.cluster_arn,
                    "capacityProviders": [],
                    "defaultCapacityProviderStrategy": [],
                },
            },
            # TODO lower this permissions
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
        )
        lame_hack.node.add_dependency(capacity_provider)
        lame_hack.node.add_dependency(cluster)

        # Create an ECS task definition with our Docker image
        task_definition = ecs.Ec2TaskDefinition(self, "ecstaskdefinition")
        container_definition = task_definition.add_container(
            "ecscontainer", image=container_image, **container_settings
        )
        # TODO lower this permissions
        task_definition.task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        )
        task_definition.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

        # Create the Amazon S3 input and output buckets
        input_bucket = s3.Bucket(
            self,
            "bucketinput",
            bucket_name=input_bucket_name,
            versioned=False,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        output_bucket = s3.Bucket(
            self,
            "bucketoutput",
            bucket_name=output_bucket_name,
            versioned=False,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Create the Amazon Lambda function for transforming the input from bucket information to the container inputs
        function = lambda_.Function(
            self,
            "inputlambda",
            code=lambda_.Code.from_inline(lambda_function_code),
            handler="index.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            environment={
                "CAPACITY_PROVIDER_NAME": capacity_provider.name,
                "CLUSTER_NAME": cluster.cluster_arn,
                "CONTAINER_NAME": container_definition.container_name,
                "REGION_NAME": self.region,
                # TODO flaky, why can't we pass the ARN directly ?
                "OUTPUT_BUCKET_NAME": output_bucket.bucket_name,
                "TASK_DEFINITION": task_definition.task_definition_arn,
            },
        )
        # Add an S3 object creation trigger for the function
        function.add_event_source(
            lambda_event_sources.S3EventSource(
                input_bucket, events=[s3.EventType.OBJECT_CREATED]
            )
        )
        # TODO fix this for less permissions
        function.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonECS_FullAccess")
        )
        function.apply_removal_policy(cdk.RemovalPolicy.DESTROY)


app = cdk.App()
CdkDemoStack(app, "CdkDemoStack")
app.synth()

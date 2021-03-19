# What is this ?

A simple toy application, which looks for new files in a given Amazon S3 bucket, allocates Amazon EC2 compute resource for processing them via a Docker container, and write the results to another Amazon S3 bucket.

## Prerequisites

* Linux Docker (on Ubuntu 18.04+ it's sufficient to do `sudo apt install docker.io` if you don't have docker installed already)

# TODO

- [ ] Automation with aws cli / cloudformation
- [ ] Better (more fine grained) IAM permissions
- [ ] Logging

# Setting up

## General information

All the stages here are set up using the us-east-1 region, you can change it to something else (by changing the url region).

If you are doing the local console stuff via the docker, you can simply run ./run.sh after git cloning this repository, then running aws configure to setup the configuration.

## Create an Amazon ECR Repository

https://console.aws.amazon.com/ecr/repositories?region=us-east-1

Create repository
  Repository name: demorepository
  Create repository

## Configure your local docker to push to it

1. Make sure you have aws cli configured with your credentials.
2. Click on demorepository in the above URL and then view push commands, 

## Create an Amazon ECS Cluster

https://us-east-1.console.aws.amazon.com/ecs/home?region=us-east-1#/clusters

- Create Cluster
  - EC2 Linux + Networking
  - Next Step
  - Cluster name: democluster
  - EC2 Instance Type: t2.micro
  - Create

## Create an Amazon ECS Cluster Capacity Provider

https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/democluster/capacityProviders

- Create
  - Capacity provider name: democlustercapacityprovider
  - Auto scaling group: Enter the one automaticly created in the ECS cluster creation.
  - Managed termiation protection: Disabled (*)

## Configure the EC2 Auto scaling group

https://console.aws.amazon.com/ec2autoscaling/home?region=us-east-1#/details

- Choose the automatic generated one from the previous step:
  - Group details: Edit
    - Desired capacity: 0
    - Maximum capacity: 4
    - Update

## Create 2 S3 Bucket (input & output)

https://s3.console.aws.amazon.com/s3/home?region=us-east-1

- Create bucket
  - Bucket name: demobucketinput
  - Create bucket

- Create bucket
  - Bucket name: demobucketoutput
  - Create bucket

## Pushing code to Amazon ECR

1. Make sure you have aws cli configured with your credentials.
2. Goto the local demo python dir.
3. Goto https://console.aws.amazon.com/ecr/repositories?region=us-east-1

Click on the demorepository, and follow the instructions under the button: View push commands

(heed the warning about the credentials being in ~/.docker/config.json)

## Create an Amazon IAM role for the ECS Task

https://console.aws.amazon.com/iam/home?#/roles

- Create role
  - Use case: Elastic Container Service -> Elastic Container Service Task
  - Next: Permissions
  - Policy: AmazonS3FullAccess
  - Next: Tags
  - Next: Review
  - Role name: demotaskrole
  - Create role

## Create an Amazon ECS Cluster Task definition

https://console.aws.amazon.com/ecs/home?region=us-east-1#/taskDefinitions

- Create new Task Definition
  - EC2
  - Next Step
  - Task Definition Name: demotask
  - Task Role: demotaskrole
  - Container: Add container
    - Container name: democontainer
    - Image: The image name from the last step in (Pushing code to Amazon ECR)
    - Memory Limits: 300
    - Add
  - Create

## Create an Amazon IAM role for the lambda function

https://console.aws.amazon.com/iam/home?#/roles

- Create role
  - Use case: Lambda -> Lambda
  - Next: Permissions
  - Policy: AmazonECS_FullAccess
  - Next: Tags
  - Next: Review
  - Role name: demolambdarole
  - Create role

## Create an Amazon Lambda function

https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions

- Create function
  - Function name: DemoHandler
  - Runtime: Python 3.8
  - Change default execution role
  - Use an existing role
  - demolambdarole
  - Create function

- \+ Add trigger:
  - S3
  - Bucket: demobucketinput
  - Event type: PUT
  - Acknowledge Recursive Invocation
  - Add

- Code
  - lambda_function.py (check the various configurations)
---
```python
import boto3

client = boto3.client('ecs')

capacityProvider = 'democlustercapacityprovider'
cluster = 'democluster'
containername = 'democontainer'
regionname = 'us-east-1'
outputbucketname = 'demobucketoutput'
taskdefinition = 'demotask'

def lambda_handler(event, context):
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_name = event['Records'][0]['s3']['object']['key']
    task = client.run_task(
        capacityProviderStrategy=[
            {
                'capacityProvider': capacityProvider,
            },
        ],
        cluster=cluster',
        overrides={
            'containerOverrides': [
                {
                    'name': containername,
                    'environment': [
                        {
                            'name': 'REGION_NAME',
                            'value': regionname
                        },
                        {
                            'name': 'INPUT_BUCKET_NAME',
                            'value': bucket_name
                        },
                        {
                            'name': 'INPUT_OBJECT_NAME',
                            'value': object_name
                        },
                        {
                            'name': 'OUTPUT_BUCKET_NAME',
                            'value': outputbucketname
                        }
                    ],
                }
            ]
        },
        taskDefinition=taskdefinition
    )
    return {
        'statusCode': 204,
    }
```
---
  - Deploy

# Test

1. Copy a file to the input bucket:

```bash
touch test
aws s3 cp test s3://demobucketinput/ 
```

2. Go to Amazon ECS cluster view and see a new pending EC2 task

https://us-east-1.console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/democluster

3. After the task finishes, an output file test should be in the output bucket with blah as contenst:

```bash
aws s3 cp s3://demobucketoutput/test -
```

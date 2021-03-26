# What is this ?

A simple toy PoC demo, which looks for new files in a given Amazon S3 bucket, allocates Amazon EC2 compute resource for processing them via a Docker container running on an elastic cluster ECS, and write the results to another Amazon S3 bucket.

The infrastructure is deployed via AWS CDK.

# Prerequisites

* Linux Docker (on Ubuntu 18.04+ it's sufficient to do `sudo apt install docker.io` if you don't have docker installed already)

# Layout

[cdk](cdk) - The directory containing the instructions for deploying the infrastructure for the demo.  
[python](python) - The source code of the application that handles the data in the file from the bucket.

# Running

You can manually install the required prerequisites for installing CDK, or you can just run the ```./run.sh``` script in this directory which setups the required environment.

It may take a few minutes the first time as it is building the docker image.

Follow the instructions in the [cdk/README.md](cdk/README.md) and [python/README.md](python/README.md) files.

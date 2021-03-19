# What is this ?

A simple toy PoC application, which looks for new files in a given Amazon S3 bucket, allocates Amazon EC2 compute resource for processing them via a Docker container, and write the results to another Amazon S3 bucket.

The application is deployed via AWS CDK.

# Prerequisites

* Linux Docker (on Ubuntu 18.04+ it's sufficient to do `sudo apt install docker.io` if you don't have docker installed already)

# Layout

[cdk](cdk) - The directory containing the instructions for deploying the application.  
[python](python) - The source code of the application.

# Running

Run the ```./run.sh``` script in this directory. It may take a few minutes the first time as it is building the docker image.

Follow the instructions in the cdk/README.md file.

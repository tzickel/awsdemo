# What is this ?

A simple toy PoC application, which looks for new files in a given Amazon S3 bucket, allocates Amazon EC2 compute resource for processing them via a Docker container, and write the results to another Amazon S3 bucket.

# Prerequisites

If you are running this script from the docker image provided above, you already have everything needed included.

* Python 3.6 (or above)
* AWS CLI
* AWS CDK 1.95.0
* Linux Docker (on Ubuntu 18.04+ it's sufficient to do `sudo apt install docker.io` if you don't have docker installed already)

# TODO

- [ ] More logging points ?
- [ ] More fine grained permissions

# Install

1. Install the requirements (do it in a virtual environment if you are not running it inside a container):

```bash
pip3 install -r requirements.txt
```

2. Setup your AWS environment, especially the AWS Access Key ID, AWS Secret Access Key and Default region name:

```bash
aws configure
```

3. The first time you are deploying the project, you need to bootstrap the environment first:

```bash
cdk bootstrap
```

4. Deploy the project:

```bash
cdk deploy
```

# Check it works

1. Create a file:

```bash
touch 1
```

2. Copy it to the input bucket:

```bash
aws s3 cp 1 s3://cdkdemoinput/
```

3. Wait for processing, if the cluster is cold it might take a few minutes, and check the output file, should be blah:

```bash
aws s3 cp s3://cdkdemooutput/1 -
```

# Uninstall

```bash
cdk destroy
```

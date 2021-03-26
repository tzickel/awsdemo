# What is this ?

A template for an application wrapped in Docker which gets an input and output object in buckets.

# Modifing

If you want to use this code as a template:

1. Make sure the [Dockerfile](Dockerfile) points to the correct Python version you need.

2. Put your required packages in the [requirements.txt](requirements.txt) file.

3. Put your logic in [run.py](run.py) in the process function, it's input is the input object data, and it returns the output object data.

4. Once you modify this directory, run the CDK's deploy and it will package it and deploy it on the cluster.

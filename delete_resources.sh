#!/bin/bash

athena_stack_name="athena_name"
glue_stack_name="glue_name"
sdy_stack_name="sdy_name"
S3_BUCKET_NAME="your_s3_bucket_name"

aws cloudformation delete-stack --stack-name ${athena_stack_name}
 
aws cloudformation delete-stack --stack-name ${glue_stack_name}
 
aws cloudformation delete-stack --stack-name "${sdy_stack_name}-sdy"

# not recommended but will use this for now
aws s3 rb s3://${S3_BUCKET_NAME} --force

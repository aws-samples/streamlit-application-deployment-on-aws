#!/bin/bash

athena_stack_name="athena_name"
glue_stack_name="glue_name"
syd_stack_name="syd_name"
S3_BUCKET_NAME="your_s3_bucket_name"

echo "deleting ${athena_stack_name}"
aws cloudformation delete-stack --stack-name ${athena_stack_name} > /dev/null

echo "deleting ${glue_stack_name}"
aws cloudformation delete-stack --stack-name ${glue_stack_name} > /dev/null

echo "deleting ${syd_stack_name}"
aws cloudformation delete-stack --stack-name "${syd_stack_name}" > /dev/null

# not recommended but will use this for now
echo "deleting s3://${S3_BUCKET_NAME}"
aws s3 rb s3://${S3_BUCKET_NAME} --force > /dev/null

echo "restore delete_resources.sh"
git checkout -- delete_resources.sh
git checkout -- deployment/sagemaker-dashboards-for-ml/examples/yahoo-finance/dashboard/script/config.py

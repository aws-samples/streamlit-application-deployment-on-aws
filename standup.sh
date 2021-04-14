#!/bin/bash

stack_name=streamlit-dashboard

# Default aws region
AWS_DEFAULT_REGION=$(aws configure list | grep region | awk '{print $2}')

#  Variables set for stack
S3_BUCKET_NAME=${stack_name}-$(uuidgen | cut -d '-' -f 5)
DATABASE_NAME=${stack_name}-blog
GLUE_CRAWLER_NAME=${stack_name}-glue-cralwer
TABLE_NAME=$(echo ${DATABASE_NAME} | tr - _)

# Coginto user paramater
COGNITO_USER=XYZ@XYZ.com

echo "stack name=${stack_name}"
echo "bucket name=${S3_BUCKET_NAME}" 
echo "crawler name=${GLUE_CRAWLER_NAME}"
echo "database name=${DATABASE_NAME}"
echo "table name= ${TABLE_NAME}"
echo "region=${AWS_DEFAULT_REGION}"

echo "Downloading and loading the data into S3"

# must be lower case for s3
S3_BUCKET_NAME=$(echo "$S3_BUCKET_NAME" | awk '{print tolower($0)}')

aws s3 mb s3://${S3_BUCKET_NAME}

python3 ./script/yahoo_idx.py

aws s3 sync ./data s3://${S3_BUCKET_NAME}

rm -rf ./data

echo "Building the Athena Workgroup"

aws cloudformation create-change-set --stack-name ${stack_name}-athena --change-set-name ImportChangeSet --change-set-type IMPORT \
--resources-to-import "[{\"ResourceType\":\"AWS::Athena::WorkGroup\",\"LogicalResourceId\":\"AthenaPrimaryWorkGroup\",\"ResourceIdentifier\":{\"Name\":\"primary\"}}]" \
--template-body file://cfn/01-athena.yaml --parameters ParameterKey="DataBucketName",ParameterValue=${S3_BUCKET_NAME}

sleep 10

aws cloudformation execute-change-set --change-set-name ImportChangeSet --stack-name ${stack_name}-athena

echo "Building Glue Crawler"

aws cloudformation create-stack --stack-name ${stack_name}-glue \
--template-body file://cfn/02-crawler.yaml --capabilities CAPABILITY_NAMED_IAM \
--parameters ParameterKey=RawDataBucketName,ParameterValue=${S3_BUCKET_NAME} \
ParameterKey=CrawlerName,ParameterValue=${GLUE_CRAWLER_NAME}

echo "Setting up the dasboard components"

cd ./deployment/sagemaker-dashboards-for-ml

cd ./cloudformation/deployment/self-signed-certificate/  && pip install -r requirements.txt -t ./src/site-packages
cd ../../..
cd ./cloudformation/deployment/string-functions/ && pip install -r requirements.txt -t ./src/site-packages
cd ../../..
cd ./cloudformation/assistants/solution-assistant/ && pip install -r requirements.txt -t ./src/site-packages
cd ../../..
cd ./cloudformation/assistants/bucket-assistant/ && pip install -r requirements.txt -t ./src/site-packages
cd ../../../..

echo "Packaging up in Cloudformation and then creating the stack"

aws cloudformation package \
--template-file ./sagemaker-dashboards-for-ml/cloudformation/template.yaml \
--s3-bucket ${S3_BUCKET_NAME} \
--s3-prefix cfn \
--output-template-file ../deployment/sagemaker-dashboards-for-ml/packaged.yaml

aws cloudformation create-stack \
--stack-name "${stack_name}-sdy" \
--template-body file://./sagemaker-dashboards-for-ml/packaged.yaml \
--capabilities CAPABILITY_IAM \
--parameters ParameterKey=ResourceName,ParameterValue=streamlit-dashboard-cfn-resource \
ParameterKey=SageMakerNotebookGitRepository,ParameterValue=https://github.com/aws-samples/streamlit-application-deployment-on-aws.git \
ParameterKey=CognitoAuthenticationSampleUserEmail,ParameterValue=${COGNITO_USER}  --disable-rollback

echo "Writing environment variables to the config file for the streamlit-package"
cd ..

config_file=deployment/sagemaker-dashboards-for-ml/examples/yahoo-finance/dashboard/src/config.py

sed -i -e "s your_region_name ${AWS_DEFAULT_REGION} g" ${config_file}
sed -i -e "s your_bucket_name ${S3_BUCKET_NAME} g"  ${config_file}
sed -i -e "s your_database_name ${DATABASE_NAME} g"  ${config_file}
sed -i -e "s your_table_name ${TABLE_NAME} g"  ${config_file}

rm -rf ${config_file}-e

echo "Writing environment variables to delete the resources file"

sed -i -e "s athena_name ${stack_name}-athena  g" delete_resources.sh
sed -i -e "s glue_name ${stack_name}-glue  g" delete_resources.sh
sed -i -e "s sdy_name ${stack_name}-sdy g" delete_resources.sh
sed -i -e "s your_s3_bucket_name ${S3_BUCKET_NAME} g" delete_resources.sh

rm -rf delete_resources.sh-e

echo "Kicking off glue craweler..."
aws glue start-crawler --name ${GLUE_CRAWLER_NAME}

echo "Complete"

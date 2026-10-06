# Personal Glue ETL with AWS CDK

Simple AWS Glue ETL project created for learning AWS IAM, Glue, S3 and IaC.

## Architecture

S3 Input
    ↓
AWS Glue Job
    ↓
Transformation
    ↓
S3 Output

## AWS Resources

The CDK stack creates:

- S3 bucket
- Glue IAM execution role
- Glue ETL job
- S3 permissions
- CloudWatch logging permissions

## Glue IAM Role

Role:

personal-glue-etl-role

Trust:

glue.amazonaws.com

Permissions:

- s3:GetObject
- s3:PutObject
- s3:ListBucket
- CloudWatch Logs permissions

## Glue Job

Job name:

personal-test-glue-job

The job:

1. Reads CSV data from S3
2. Adds 1 to the quantity column
3. Writes transformed data back to S3

## Deployment

Initial deployment is performed using AWS CDK.

GitHub Actions OIDC deployment will be added later.

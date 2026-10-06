from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_iam as iam,
    aws_glue as glue,
    aws_s3_deployment as s3deploy,
    CfnOutput,
)
from constructs import Construct


class PersonalGlueETLStack(Stack):

    def __init__(self, scope, construct_id, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ============================================================
        # CONFIGURATION
        # ============================================================

        AWS_ACCOUNT_ID = "493272324412"
        AWS_REGION = "us-east-2"

        GITHUB_REPOSITORY = "hancy121/personal-glue-etl-iac"

        # IAM role names
        PROD_GITHUB_OIDC_ROLE = "personal-prod-github-oidc-role"
        PROD_LAMBDA_ROLE_NAME = "personal-prod-glue-role"

        # ============================================================
        # 1. S3 BUCKET
        # ============================================================

        bucket = s3.Bucket(
            self,
            "GlueDataBucket",

            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,

            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,

            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        # ============================================================
        # 2. GITHUB OIDC PROVIDER
        #
        # This allows GitHub Actions to authenticate with AWS
        # without storing AWS access keys in GitHub.
        # ============================================================

        github_oidc_provider = iam.OpenIdConnectProvider(
            self,
            "GitHubOIDCProvider",

            url="https://token.actions.githubusercontent.com",

            client_ids=[
                "sts.amazonaws.com"
            ],
        )

        # ============================================================
        # 3. GITHUB ACTIONS IAM ROLE
        #
        # This is equivalent to:
        #
        # PROD_GITHUB_OIDC_ROLE
        #
        # GitHub assumes this role through OIDC.
        # ============================================================

        github_role = iam.Role(
            self,
            "GitHubDeploymentRole",

            role_name=PROD_GITHUB_OIDC_ROLE,

            assumed_by=iam.WebIdentityPrincipal(
                github_oidc_provider
            ).with_conditions(
                {
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud":
                            "sts.amazonaws.com"
                    },

                    "StringLike": {
                        "token.actions.githubusercontent.com:sub":
                            f"repo:{GITHUB_REPOSITORY}:*"
                    },
                }
            ),

            description=(
                "GitHub Actions OIDC deployment role "
                "for personal Glue ETL project"
            ),
        )

        # ============================================================
        # 4. GITHUB DEPLOYMENT ROLE PERMISSIONS
        #
        # These permissions allow GitHub Actions/CDK to create
        # and update the infrastructure.
        # ============================================================

        github_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,

                actions=[
                    # CloudFormation
                    "cloudformation:*",

                    # S3 required for CDK assets and stack
                    "s3:*",

                    # Glue
                    "glue:*",

                    # IAM
                    "iam:GetRole",
                    "iam:CreateRole",
                    "iam:DeleteRole",
                    "iam:PutRolePolicy",
                    "iam:DeleteRolePolicy",
                    "iam:AttachRolePolicy",
                    "iam:DetachRolePolicy",
                    "iam:PassRole",
                    "iam:GetPolicy",
                    "iam:CreatePolicy",
                    "iam:DeletePolicy",

                    # OIDC provider
                    "iam:GetOpenIDConnectProvider",
                    "iam:CreateOpenIDConnectProvider",
                    "iam:DeleteOpenIDConnectProvider",
                    "iam:UpdateOpenIDConnectProviderThumbprint",

                    # Lambda is used by CDK BucketDeployment
                    "lambda:*",

                    # CloudWatch Logs
                    "logs:*",
                ],

                resources=["*"],
            )
        )

        # ============================================================
        # 5. GLUE EXECUTION ROLE
        #
        # Equivalent to the company's:
        #
        # PROD_LAMBDA_ROLE_NAME
        #
        # This role is assumed by AWS Glue.
        # ============================================================

        glue_role = iam.Role(
            self,
            "GlueExecutionRole",

            role_name=PROD_LAMBDA_ROLE_NAME,

            assumed_by=iam.ServicePrincipal(
                "glue.amazonaws.com"
            ),

            description=(
                "IAM execution role for personal Glue ETL job"
            ),
        )

        # ============================================================
        # 6. GLUE ROLE - S3 PERMISSIONS
        #
        # Equivalent to:
        #
        # s3:GetObject
        # s3:PutObject
        # s3:DeleteObject
        # s3:ListBucket
        # ============================================================

        bucket.grant_read_write(glue_role)

        # ============================================================
        # 7. GLUE ROLE - CLOUDWATCH LOG PERMISSIONS
        # ============================================================

        glue_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,

                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],

                resources=["*"],
            )
        )

        # ============================================================
        # 8. UPLOAD GLUE SCRIPT TO S3
        # ============================================================

        s3deploy.BucketDeployment(
            self,
            "DeployGlueScript",

            sources=[
                s3deploy.Source.asset("../glue")
            ],

            destination_bucket=bucket,

            destination_key_prefix="glue-scripts",
        )

        # ============================================================
        # 9. CREATE GLUE JOB
        # ============================================================

        glue_job = glue.CfnJob(
            self,
            "PersonalGlueJob",

            name="personal-test-glue-job",

            role=glue_role.role_arn,

            glue_version="5.0",

            worker_type="G.1X",

            number_of_workers=2,

            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",

                script_location=(
                    f"s3://{bucket.bucket_name}/"
                    "glue-scripts/glue_job.py"
                ),

                python_version="3",
            ),

            default_arguments={
                "--job-language": "python",

                "--enable-metrics": "",

                "--enable-continuous-cloudwatch-log": "true",

                "--input_path": (
                    f"s3://{bucket.bucket_name}/input/"
                ),

                "--output_path": (
                    f"s3://{bucket.bucket_name}/output/"
                ),
            },
        )

        # ============================================================
        # 10. STACK OUTPUTS
        # ============================================================

        CfnOutput(
            self,
            "GitHubOIDCRoleArn",

            value=github_role.role_arn,

            description=(
                "GitHub Actions OIDC deployment role ARN"
            ),
        )

        CfnOutput(
            self,
            "GitHubOIDCRoleName",

            value=PROD_GITHUB_OIDC_ROLE,

            description=(
                "GitHub Actions OIDC deployment role name"
            ),
        )

        CfnOutput(
            self,
            "GlueRoleArn",

            value=glue_role.role_arn,

            description=(
                "IAM role used by the Glue job"
            ),
        )

        CfnOutput(
            self,
            "GlueRoleName",

            value=PROD_LAMBDA_ROLE_NAME,

            description=(
                "Glue execution IAM role name"
            ),
        )

        CfnOutput(
            self,
            "BucketName",

            value=bucket.bucket_name,

            description=(
                "S3 bucket used by the Glue ETL job"
            ),
        )

        CfnOutput(
            self,
            "GlueJobName",

            value=glue_job.name,

            description=(
                "Glue ETL job name"
            ),
        )

        CfnOutput(
            self,
            "InputPath",

            value=f"s3://{bucket.bucket_name}/input/",

            description=(
                "Input CSV location"
            ),
        )

        CfnOutput(
            self,
            "OutputPath",

            value=f"s3://{bucket.bucket_name}/output/",

            description=(
                "Output CSV location"
            ),
        )

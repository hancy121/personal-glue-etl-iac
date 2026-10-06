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

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)

        # =========================================================
        # 1. S3 BUCKET
        # =========================================================

        bucket = s3.Bucket(
            self,
            "GlueDataBucket",

            removal_policy=RemovalPolicy.DESTROY,

            auto_delete_objects=True,

            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,

            encryption=s3.BucketEncryption.S3_MANAGED,

        )

        # =========================================================
        # 2. GLUE IAM EXECUTION ROLE
        # =========================================================

        glue_role = iam.Role(
            self,
            "GlueExecutionRole",

            role_name="personal-glue-etl-role",

            assumed_by=iam.ServicePrincipal(
                "glue.amazonaws.com"
            ),

            description="IAM execution role for personal Glue ETL job",
        )

        # =========================================================
        # 3. S3 PERMISSIONS
        # =========================================================

        # Allows Glue to read and write objects in our bucket.
        bucket.grant_read_write(glue_role)

        # =========================================================
        # 4. CLOUDWATCH LOG PERMISSIONS
        # =========================================================

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

        # =========================================================
        # 5. UPLOAD GLUE SCRIPT TO S3
        # =========================================================

        s3deploy.BucketDeployment(
            self,
            "DeployGlueScript",

            sources=[
                s3deploy.Source.asset("../glue")
            ],

            destination_bucket=bucket,

            destination_key_prefix="glue-scripts",
        )

        # =========================================================
        # 6. CREATE GLUE JOB
        # =========================================================

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

        # =========================================================
        # 7. OUTPUTS
        # =========================================================

        CfnOutput(
            self,
            "BucketName",

            value=bucket.bucket_name,

            description="S3 bucket used by the Glue ETL job",
        )

        CfnOutput(
            self,
            "GlueRoleArn",

            value=glue_role.role_arn,

            description="IAM role used by the Glue job",
        )

        CfnOutput(
            self,
            "GlueJobName",

            value=glue_job.name,

            description="Glue ETL job name",
        )

        CfnOutput(
            self,
            "InputPath",

            value=f"s3://{bucket.bucket_name}/input/",

            description="Input CSV location",
        )

        CfnOutput(
            self,
            "OutputPath",

            value=f"s3://{bucket.bucket_name}/output/",

            description="Output CSV location",
        )

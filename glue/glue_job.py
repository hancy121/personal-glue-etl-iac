import sys

from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.sql.functions import col


# =========================================================
# GET ARGUMENTS
# =========================================================

args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "input_path",
        "output_path",
    ],
)


# =========================================================
# INITIALIZE GLUE
# =========================================================

sc = SparkContext()

glueContext = GlueContext(sc)

spark = glueContext.spark_session

job = Job(glueContext)

job.init(
    args["JOB_NAME"],
    args,
)


print("========================================")
print("Personal Glue ETL Job Started")
print("========================================")

print(
    f"Input path: {args['input_path']}"
)

print(
    f"Output path: {args['output_path']}"
)


# =========================================================
# READ CSV FROM S3
# =========================================================

print("Reading input CSV...")

df = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(args["input_path"])
)

print("Input data:")

df.show()


# =========================================================
# TRANSFORMATION
# =========================================================

print("Transforming data...")

transformed_df = df.withColumn(
    "quantity_plus_one",
    col("quantity").cast("int") + 1
)

print("Transformed data:")

transformed_df.show()


# =========================================================
# WRITE RESULT TO S3
# =========================================================

print("Writing output to S3...")

(
    transformed_df.write
    .mode("overwrite")
    .option("header", "true")
    .csv(args["output_path"])
)


print("========================================")
print("Personal Glue ETL Job Completed")
print("========================================")


# =========================================================
# COMPLETE JOB
# =========================================================

job.commit()

from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import *
from pyspark.sql.window import Window
import os
import sys

nsd_id = sys.argv[1]
kafka_topic = sys.argv[2]
#os.environ["HADOOP_CONF_DIR"] = "/opt/cloudera/parcels/CDH-6.3.2-1.cdh6.3.2.p0.1605554/lib/spark/conf/yarn-conf"
spark = SparkSession.builder.master("yarn").appName("AIML-process-kafka-" + kafka_topic).getOrCreate()

df_metric_raw = spark.read.load("hdfs://master.awe.polito.it:8020/user/worker/metrics/" + nsd_id + "/metric_" + kafka_topic,
	format="csv", inferSchema="true", header="true")
df_il_raw = spark.read.load("hdfs://master.awe.polito.it:8020/user/worker/metrics/" + nsd_id +"/il_" + kafka_topic,
	format="csv", inferSchema="true", header="true")
#df_metric_raw.show(5)
#df_il_raw.show(5)
window = Window.partitionBy("nsid").orderBy("timestamp").rowsBetween(1,1)
df_il_w_null = df_il_raw \
	.withColumn("end_timestamp_null", lag(df_il_raw["timestamp"], -1).over(window)) \
	.withColumnRenamed("timestamp","start_timestamp").withColumnRenamed("nsid", "nsid_il")

df_il = df_il_w_null \
	.withColumn("end_timestamp", when(df_il_w_null.end_timestamp_null.isNotNull(),
									  df_il_w_null.end_timestamp_null).otherwise(current_timestamp())) \
	.drop(df_il_w_null.end_timestamp_null)
#df_il.show(truncate=False)

df_metric = df_metric_raw \
	.groupBy(["metric_name", "metric_value", "nsid", "timestamp"]) \
	.pivot("metric_name") \
	.mean("metric_value")
#df_metric.show(5, truncate=False)

cond = [df_metric.nsid == df_il.nsid_il,
	df_metric.timestamp >= df_il.start_timestamp,
	df_metric.timestamp < df_il.end_timestamp]
df = df_metric.join(df_il, cond, "left")
#df.show(truncate=False)

drop_cols = ["metric_name","metric_value","start_timestamp","end_timestamp","nsid_il"]
df.drop(*drop_cols).orderBy("timestamp").coalesce(1).write.mode("overwrite").save("hdfs://master.awe.polito.it:8020/user/worker/metrics/" + nsd_id + "/complete_" + kafka_topic,
	format="csv", header="true")

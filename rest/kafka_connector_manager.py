from pyspark.sql import SparkSession, Window
from pyspark.sql.types import *
from pyspark.sql.functions import *
from config import app
from rest.utils import get_scoped_session
import os.path
import subprocess
from model import DatasetCollector, CollectorStatus
from datetime import datetime

general_schema = StructType() \
    .add("type_message", StringType(), False)

il_schema = StructType() \
    .add("type_message", StringType(), False) \
    .add("metric", StructType([
    StructField("__name__", StringType()),
    StructField("nsId", StringType()),
    StructField("vnfdId", StringType()),
]), False) \
    .add("value", StringType())

metric_schema = StructType() \
    .add("type_message", StringType(), False) \
    .add("metric", StructType([
    StructField("__name__", StringType()),
    StructField("nsId", StringType()),
    StructField("vnfdId", StringType()),
]), False) \
    .add("value", ArrayType(StringType()))


def get_spark():
    return SparkSession.builder.getOrCreate()


def build_path(df_type, nsd_id, kafka_topic):
    base_path = os.path.join(app.config["HDFS_NAMENODE"] + \
                             app.config["HDFS_ROOT_DIR"],
                             app.config["HDFS_METRICS_DIR"],
                             nsd_id)
    if df_type == "il":
        path = os.path.join(base_path, "il_" + kafka_topic)
    elif df_type == "metric":
        path = os.path.join(base_path, "metric_" + kafka_topic)
    else:
        raise ValueError("df_type can only be 'metric' or 'il'")
    return path


def start_streaming(kafka_topic, kafka_server, nsd_id):
    kafka_raw_df = get_spark().readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_server) \
        .option("subscribe", kafka_topic) \
        .option("startingOffsets", "earliest") \
        .load()
    kafka_df = kafka_raw_df.select(kafka_raw_df.value.cast(StringType()), kafka_raw_df.timestamp)
    df = kafka_df.select("value", from_json(kafka_df.value, general_schema).alias("json"), "timestamp")
    df_filter_il = df \
        .filter(df.json.type_message == "nsStatusMetrics") \
        .select(from_json(df.value, il_schema).alias("json_il"), "timestamp")
    df_filter_metric = df \
        .filter(df.json.type_message == "metric") \
        .select(from_json(df.value, metric_schema).alias("json_metric"), "timestamp")
    df_il = df_filter_il.select(
        df_filter_il.json_il.value.alias("il"),
        df_filter_il.json_il.metric.nsId.alias("nsid"),
        df_filter_il.timestamp)
    df_metric = df_filter_metric.select(
        df_filter_metric.json_metric.metric["__name__"].alias("metric_name"),
        df_filter_metric.json_metric.value.getItem(1).alias("metric_value"),
        df_filter_metric.json_metric.metric.nsId.alias("nsid"),
        df_filter_metric.timestamp)
    il_query = df_il \
        .writeStream \
        .format("csv") \
        .option("path", build_path("il", nsd_id, kafka_topic)) \
        .option("checkpointLocation", os.path.join(build_path("il", nsd_id, kafka_topic), ".checkpoint")) \
        .option("header", True) \
        .queryName("il_" + kafka_topic) \
        .trigger(processingTime='60 seconds') \
        .start()
    metric_query = df_metric \
        .writeStream \
        .format("csv") \
        .option("path", build_path("metric", nsd_id, kafka_topic)) \
        .option("checkpointLocation", os.path.join(build_path("metric", nsd_id, kafka_topic), ".checkpoint")) \
        .option("header", True) \
        .queryName("metric_" + kafka_topic) \
        .trigger(processingTime='15 seconds') \
        .start()
    return metric_query.id, il_query.id


def stop_streaming(metric_query_id, il_query_id):
    spark = get_spark()
    spark.streams.get(metric_query_id).stop()
    spark.streams.get(il_query_id).stop()


def process_metrics(engine, collector_id, timeout=None):
    Session = get_scoped_session(engine)
    session = Session()
    collector = session.query(DatasetCollector) \
        .get(collector_id)
    if collector is None:
        return

    try:
        # Launch processing with spark-submit
        completed_process = subprocess.run(
            args=["./rest-spark-submit_light.sh",
                  "spark-process-ns.py",
                  collector.nsd_id,
                  collector.kafka_topic],
            text=True,
            timeout=timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        if completed_process.returncode != 0:
            print(completed_process.stdout)
            raise Exception("Spark-submit exited with a non-zero exit code.",
                            completed_process.returncode)
    except Exception as e:
        print("Dataset processing for nsd_id ", collector.nsd_id,
              "and kafka topic ", collector.kafka_topic, "failed:",
              str(e))
        collector.status = CollectorStatus.error
    else:
        collector.termination_timestamp = datetime.now()
        collector.status = CollectorStatus.terminated
    finally:
        session.commit()
        Session.remove()


def print_streaming_status():
    spark = get_spark()
    sqm = spark.streams
    print([q.status for q in sqm.active])

def get_dataset_dict_from_nsd(nsd_id):
    spark = get_spark()
    df = spark.read.load("hdfs://master.awe.polito.it:8020/user/worker/metrics/" + nsd_id + "/complete_*",
               format="csv", inferSchema="true", header="true")
    #ordered_df = df.orderBy("nsid", "timestamp")
    return [row.asDict() for row in df.collect()]
#!/bin/bash
SPARK_HOME=/opt/cloudera/parcels/CDH/lib/spark
GPL_LIBS=/opt/cloudera/parcels/GPLEXTRAS/jars
BigDL_HOME=~/bigdl
VENV_HOME=${BigDL_HOME}
PYSPARK_PYTHON=./environment/bin/python \
${SPARK_HOME}/bin/spark-submit \
    --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./environment/bin/python \
    --conf spark.yarn.appMasterEnv.PYSPARK_DRIVER_PYTHON=./environment/bin/python \
    --master yarn \
    --deploy-mode cluster \
    --executor-memory 2g \
    --driver-memory 1g \
    --executor-cores 2 \
    --num-executors 2 \
    --properties-file ${BigDL_HOME}/conf/spark-bigdl.conf \
    --archives ${VENV_HOME}/environment.tar.gz#environment \
    "$@"

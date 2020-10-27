#!/bin/bash
SPARK_HOME=/opt/cloudera/parcels/CDH/lib/spark
GPL_LIBS=/opt/cloudera/parcels/GPLEXTRAS/jars
BigDL_HOME=~/bigdl
BigDL_VERSION=0.11.0
PYTHON_API_PATH=${BigDL_HOME}/lib/bigdl-${BigDL_VERSION}-python-api.zip
BigDL_JAR_PATH=${BigDL_HOME}/lib/bigdl-SPARK_2.4-${BigDL_VERSION}-jar-with-dependencies.jar
PYTHONPATH=${PYTHON_API_PATH}:$PYTHONPATH
VENV_HOME=${BigDL_HOME}
PYSPARK_PYTHON=./environment/bin/python \
${SPARK_HOME}/bin/spark-submit \
    --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./environment/bin/python \
    --conf spark.yarn.appMasterEnv.PYSPARK_DRIVER_PYTHON=./environment/bin/python \
    --master yarn \
    --deploy-mode cluster \
    --executor-memory 2g \
    --driver-memory 2g \
    --executor-cores 2 \
    --num-executors 3 \
    --properties-file ${BigDL_HOME}/conf/spark-bigdl.conf \
    --jars ${BigDL_JAR_PATH} \
    --py-files ${PYTHON_API_PATH} \
    --archives ${VENV_HOME}/environment.tar.gz#environment \
    --conf spark.driver.extraClassPath=bigdl-SPARK_2.4-${BigDL_VERSION}-jar-with-dependencies.jar \
    --conf spark.executor.extraClassPath=bigdl-SPARK_2.4-${BigDL_VERSION}-jar-with-dependencies.jar \
    "$@"

#    --conf "spark.yarn.jars=file://${SPARK_HOME}/jars/*,file://${GPL_LIBS}/*" \
#    --conf "spark.driver.extraLibraryPath=/opt/cloudera/parcels/CDH/lib/hadoop/lib/native:/opt/cloudera/parcels/GPLEXTRAS/lib/hadoop/lib/native" \
#    --conf "spark.executor.extraLibraryPath=/opt/cloudera/parcels/CDH/lib/hadoop/lib/native:/opt/cloudera/parcels/GPLEXTRAS/lib/hadoop/lib/native" \
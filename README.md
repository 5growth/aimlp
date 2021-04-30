### Project information
5GROWTH is funded by the European Union’s Research and Innovation Programme Horizon 2020 under Grant Agreement no. 856709


Call: H2020-ICT-2019. Topic: ICT-19-2019. Type of action: RIA. Duration: 30 Months. Start date: 1/6/2019


<p align="center">
<img src="https://upload.wikimedia.org/wikipedia/commons/b/b7/Flag_of_Europe.svg" width="100px" />
</p>

<p align="center">
<img src="https://5g-ppp.eu/wp-content/uploads/2019/06/5Growth_rgb_horizontal.png" width="300px" />
</p>
 



# 5GROWTH-AIMLP
This repository contains the code for the AI/ML platform developed in the 5Growth EU project.


The AI/ML Platform, a novel component of the 5Growth architecture, is a centralized and optimized environment to train and host AI/ML models.


Whenever an entity of the 5Gr stack needs a trained AI/ML model, it can query the AI/ML Platform in order to retrieve it.
If the model is not trained yet, a training job will be triggered and, as soon as it is completed, the link to download the trained model will be made available to the entity.


## Requirements
The AI/ML Platform works in conjunction with an Apache Hadoop cluster.
The required projects are:
- Apache HDFS
- Apache YARN
- Apache Spark (developed and tested with version 2.4)
- BigDL (for deep neural networks models)


To install BigDL, follow the [instructions](https://bigdl-project.github.io/master/#PythonUserGuide/install-without-pip/) in the project documentation.
It is suggested to build the requirements archive using 'conda pack'. The following commands can be used as example:


    #!/bin/sh
    conda create -y -n bigdl python=3.6
    conda activate bigdl
    # requirements as provided by bigdl
    conda install -y -c conda-forge --file bigdl/bin/requirements.txt
    conda pack -o environment.tar.gz
    conda deactivate bigdl
    conda remove --name bigdl --all


The application is written in Python, so a Python interpreter (version > 3.7) is required to run it.
The following packages, which can be installed using pip, are required:
- flask
- marshmallow
- marshmallow-sqlalchemy
- sqlalchemy
- flask-sqlalchemy
- flask-marshmallow
- flask-login
- pyarrow
- pyspark=2.4

## Installation
Copy the projet folder in a machine that has access to the cluster, using an user with the proper rights, i.e. can execute spark-submit and access HDFS.

Before being able to use the platform, it is required to customize the config.py and rest-spark-submit.sh files, 
according to the cluster configuration and available compute resources.
The provided files, which contain the configuration used to develop and test the platform, can be used as example.

## Usage
Run the command `python3 main.py`. The default server port is 5000.

The first time the application is started, before it can be utilized, it requires the generation of the sqlite3 database.
To do that, call `GET /reset?forced=1`.
To clean the database without deleting the registered users, use `GET /reset`.
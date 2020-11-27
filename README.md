# AI/ML Platform
The AI/ML Platform is a centralized and optimized environment to train and host AI/ML models.
It has been developed by [Politecnico di Torino](https://www.polito.it/) (IT) within the Europen project [5Growth](https://5growth.eu/) as a novel component of the 5Growth (5Gr) architecture.

Whenever an entity of the 5Gr stack needs a trained AI/ML model, it can query the AI/ML Platform in order to retrieve it.
If the model is not trained yet, a training job will be triggered and, as soon as it is completed, the link to download the trained model will be made available to the entity.

This README.md file is WIP. If you have any question feel free to contact [Corrado Puligheddu](mailto:corrado.puligheddu@polito.it)

## Requirements
The AI/ML Platform works in conjunction with an Apache Hadoop cluster.
The required components are:
- Apache YARN
- Apache Spark
- Apache HDFS
- BigDL (for neural networks models)

It is highly recommended to use Cloudera Manager to setup the cluster.
To install BigDL, follow the [instructions](https://bigdl-project.github.io/master/#PythonUserGuide/install-without-pip/) in the project documentation.
It is suggested to build the requirements archive using 'conda pack'. The following code can be used as example:


    #!/bin/sh
    
    conda create -y -n bigdl python=3.6
    conda activate bigdl
    # requirements are provided by bigdl
    conda install -c conda-forge bigdl/bin/requirements.txt
    conda pack -o environment.tar.gz
    conda deactivate bigdl
    conda remove --name bigdl --all


The application is written in Python, so a Python interpreter (version > 3.7) is required to run it.
The following packages, which can be installed using pip, are required:
- flask
- marshmallow
- sqlalchemy
- flask-sqlalchemy
- flask-marshmallow
- flask-login
- pyarrow

## Installation
Copy the projet folder in a machine that has access to the cluster, using an user with the proper rights, i.e. can execute spark-submit and access HDFS.

Before being able to use the platform, it is required to customize the config.py and rest-spark-submit.sh files.
The provided files, that contain the configuration we used to develop and test the platform, can be used as example.

## Usage
Run the command `python3 main.py`. The default server port is 5000.

The first time the application is started, before it can be utilized, require the generation of the sqlite3 database.
To do that, call `GET /reset?forced=1`.
Now the application is fully functional. In case, after some use, you want to delete the models but not the users, you can call `GET /reset`.
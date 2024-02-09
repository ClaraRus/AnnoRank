#!/bin/bash
read -p "Please select dataset name cvs, xing, flickr or amazon: " dataset_name
sed -i~ "s/^DATANAME=.*/DATANAME=$dataset_name/" .env
docker-compose up

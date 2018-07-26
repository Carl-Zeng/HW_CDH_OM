#!/bin/bash

source_database=public_network

source_ip=172.17.16.136
source_namenode_ip=172.17.16.134
source_namenode_hostname=cscloud-rs-hadoop124.huawei.com

target_ip=172.17.1.11
target_nomenode_hostname=nameservice1


#create  target  database
target_database=${source_database}
impala-shell -i ${target_ip}   -q "drop database ${target_database} cascade"
impala-shell  -i ${target_ip}  -q  "create  database ${target_database}"

#copy data to target
sudo -u hadoop fs -rm  -R  /user/hive/warehouse/${source_database}.db
hadoop distcp   hdfs://${source_namenode_ip}:8020/user/hive/warehouse/${source_database}.db   /user/hive/warehouse/

#create  target  tables
for tb in `impala-shell  -i ${source_ip}  -q  "use  ${target_database};show  tables"  -B`
do
echo  "$tb"
schema_source=`impala-shell  -i  ${source_ip}  -q  "use  ${target_database};show create  table $tb"  -B`
schema=${schema_source/${source_namenode_ip}:8020/${target_nomenode_hostname}}
schema=${schema/${source_namenode_hostname}:8020/${target_nomenode_hostname}}
schema=${schema//\"/}}
schema=${schema/\}/}
echo ${schema}
impala-shell  -i ${target_ip}  -q  "use ${target_database};${schema}"
done

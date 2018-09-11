# -*- coding:utf-8     -*-
"""
"""

import os
#from pathlib import Path
try_times = 4  #rerun query  times
log_path = '/home/tpcds/log_5.15_add_disk_sender_size/tpcds10t_parquet'


def read_single_file_2_lines(filepath):
        print('Reading from:' +filepath+'\n' )
        file_object = open(filepath,'r')
        contents = file_object.read()  #get contents from the path
        contents_lines = contents.split('\n')
        return contents_lines


def get_all_child_file(parentPath):
        if  not(os.path.exists(parentPath)):
                return
        else :
                _filelist = []
                _filelist_tmp = os.listdir(parentPath)
                for  filename in _filelist_tmp :
                        if (os.path.isfile(parentPath + '/'  + filename)) :
                                _filelist.append(filename)
                return _filelist


def get_result_times_from_log(filePath):
        _lines = read_single_file_2_lines(filePath)
        _times = []
        for line in _lines:
                if (('Fetched' in line) and  len(line.split(' ')) >= 5 ) :
                        _times.append(line.split(' ')[4].replace('s',''))
        return _times

def get_list_avg(timelist):
        _total_time = 0
        if (len(timelist) < try_times):
                return str(_total_time)
        for time in timelist:
                _total_time += float(time)
        _avg = _total_time/len(timelist)
        return str(_avg)

#set  result  dict
_results={}

#log_path = /home/tpcds/log_5.15_add_disk_sender_size/tpcds10t_parquet
if (os.path.isfile(log_path)):
        print log_apth + " is  error!"
else :
        print "get  result  log  from path " + log_path
        file_list = get_all_child_file(log_path)
#       print file_list
        for file  in file_list :
                times = get_result_times_from_log(log_path + '/' + file)
                avg = get_list_avg(times)
                _results[file] = avg
#               print "avg:" + avg


#sorted result by  filename
_results_sorted=sorted(_results)




result_csv_name='result.csv'
if os.path.exists(result_csv_name):
        os.remove(result_csv_name)
        print "rmove path :"+ result_csv_name
result_csv = open(result_csv_name,'w')
for dict in _results_sorted:
        result_csv.write(dict + ',' + _results[dict] + '\n' )

print "write all avg into file : " + result_csv_name
result_csv.close
#file_list = get_all_child_file(log_path)
#print file_list

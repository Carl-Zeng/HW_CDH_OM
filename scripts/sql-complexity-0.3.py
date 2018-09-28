#!/usr/bin/env  python
# -*-  coding:utf-8 -*-

#
#权重以关键字操作的响应时间或者可能对任务产生性能瓶颈为基础，量化权重参考标准为：
#Schama操作一次为1；数据写入一次为5；一次Map操作为1；数据Exchange一次为5；排序一次为5；View重复调用一次为5；With子句重复调用一次为5.
#DDL权重表示了Sql脚本的结构性复杂度，DML权重表示了各子任务算子计算的复杂度；
#算法复杂度=DDL复杂度+DML复杂度;





import os,sys, getopt
import re

_dict_ddl_weight = {
  'drop' : 0.5,
  'create_view' : 0.5,
  'create_table' : 5,
  'alter' : 0.5,
  'computer' : 2,
  'view_name': 5,
  'with_name': 5
}


_dict_dml_weight = {
  'select' : 1,
  'join' : 3,
  'group' : 4,
  'distinct' : 3,
  'over' : 4,
  'order' : 5,
  'truncate' : 2,
  'insert' : 5,
  'union' : 4,
  'unionall' : 1
}



#结果字段列表，是有序排列的
_nameList = [
  'drop',
  'create_view',
  'create_table',
  'alter',
  'computer',
  'view_name',
  'with_name',
  'select',
  'join',
  'group',
  'distinct',
  'over',
  'order',
  'truncate',
  'insert',
  'union',
  'unionall',
  'dml_weight',
  'ddl_weight',
  'total_weight'
       ]


class ResultObject:
    def __init__(self,nameList):
        self.__nameList = nameList
        pass
    def get_result_data(self,result_dict,filename = 'default'):
        result=filename.rpartition('/')[2]
        for name in self.__nameList:
            try :
        	result = result + ',' + str(result_dict[name]) 
            except :
                result = result + ',' +  str(0)
        return  result
    def get_filed_name(self):
        result = 'NAME'
        for name in self.__nameList:
            result  = result + ',' +  name 
        return result
    def get_result_weight(self,*args):
        result = 'Weight'
        dicts = {}
        for di in args:
            dicts = dict(dicts,**di)
        for name in self.__nameList:
            value = 0    
            try :
                if dicts.has_key(name):
                    value = dicts[name]
            except :
                pass
            result = result + ',' + str(value)
        return result

def  init(argv):
   inputfile = ''
   try:
      opts, args = getopt.getopt(argv,"hf:")
   except getopt.GetoptError:
      print "useage: " + sys.argv[0] + ' -f  <inputfile> '
      sys.exit(2)
   if len(opts) == 0:
      print "useage: " +   sys.argv[0] + ' -f  <inputfile> '
      sys.exit()
   for opt, arg in opts:
      if opt == '-h':
         print "useage: " +  sys.argv[0] + ' -f  <inputfile> '
         sys.exit()
      elif opt in ('-f'):
         inputfile = arg
   if ( os.path.exists(inputfile)):
      return inputfile
   else :
      print inputfile + " is not a sql  file or a path! "
      sys.exit()



def read_file_2_linelist(filepath):
    file_object = open(filepath,'r')
    contents = file_object.read()  #get contents from the path
    contents_lines = contents.split('\n')
    return contents_lines   

def filtering_annotation(filepath):
    contents_list = read_file_2_linelist(filepath)
    flag = 0
    number = 0
    line_list = []
    while number < len(contents_list):
       line = contents_list[number]
       if ( line.find(r'*/') >= 0 ):
	  line = line[line.find('*/') + 2:]
          flag  = 0
       if (line.find('/*') >= 0 ):
          line = line[0:line.find('/*') ]
          flag = 1 
       if (line.find('*/') >= 0 ):
          line = line[line.find('*/') + 2:]
          flag = 0
       if (line.find('--') >= 0 ):
          line = line.split('--')[0]
       if line != '' and flag == 0:
          line_list.append(line.lower()) 
       number += 1
    return  line_list
       

#获取with as 子句中所有子句的名称以及被调用的次数
def get_with_table_names(line_list):
    contents_lines = line_list
    with_name = []
    with_name_count = {}
    total_lines =  ' '.join(contents_lines)\
                       .lower()\
                       .strip()
    words_list = total_lines.split()
    index = 0
    while  index < len(words_list)   :
        if (  words_list[index] == 'with' ):       #if 语句处理每个with子句，以‘；’为结束标志；
            with_name.append(words_list[index + 1] )
            flag = 0
            index +=2
            while 1 == 1 :
                if words_list[index].startswith('(') :
                    flag += 1
                if  words_list[index].endswith(')')  or words_list[index].endswith('),') :
                    flag -= 1
                if flag == 0 and ( words_list[index].endswith(',')  or words_list[index].endswith('),') ) :
                    with_name.append(words_list[index + 1])
                index += 1
                if   index >= len(words_list) or  words_list[index ].endswith(';') :    #若果遇到‘；’ 表示子句结束，跳出此次子循环；
                    break
        index  += 1
    for name in with_name:
        with_name_count[name] = words_list.count(name) + \
                                words_list.count(name + ')' ) +\
                                words_list.count(name + ';') +\
                                words_list.count(name + ');')  +\
                                words_list.count(name + '),') +  \
                                words_list.count(name + ',')

    name_count = len(with_name)
    total_count = 0
    for value in with_name_count.values():
        total_count += value
    result = total_count - 2 * name_count
    return result


#返回所有的view非正常调用次数
def  get_view_name_count(line_list):
    contents_lines = line_list
    total_lines = ' '.join(contents_lines)
    view_names = []
    view_name_count = {}
    words_list = ' '.join(contents_lines)\
                    .lower()\
                    .strip()\
                    .split()
    for index in range(len(words_list)):
        if index <  len(words_list) -2  and  words_list[index] == 'view' and words_list[index - 1].endswith('create') :
            view_names.append(words_list[index + 1])
    for name in view_names:
        view_name_count[name] = words_list.count(name) + \
                                words_list.count(name + ')' ) +\
                                words_list.count(name + ';') +\
                                words_list.count(name + ');')  +\
                                words_list.count(name + '),') +  \
                                words_list.count(name + ',')
    
    name_count = len(view_names)
    total_count = 0
    for value in view_name_count.values():
        total_count += value
    result = total_count - 4 * name_count
    return result


#返回create view的次数
def get_create_view_count(line_list):
    contents_lines = line_list
    total_lines = ' '.join(contents_lines)
    create_view_count = 0
    words_list = ' '.join(contents_lines)\
                    .lower()\
                    .strip()\
                    .split()
    for index in range(len(words_list)):
        if index <  len(words_list) -2  and  words_list[index] == 'view' and words_list[index - 1].endswith('create') :
            create_view_count += 1
    return create_view_count


def get_unionAll_count(line_list):
    contents_lines = line_list
    total_lines = ' '.join(contents_lines)
    unionall_count = 0
    words_list = ' '.join(contents_lines)\
                    .lower()\
                    .strip()\
                    .split()
    for index in range(len(words_list) -1 ):
        if  (words_list[index] == 'union' or words_list[index] == ')union'  ) and words_list[index + 1] == 'all' :
            unionall_count += 1
    return unionall_count
    

def get_union_count(line_list):
    contents_lines = line_list
    total_lines = ' '.join(contents_lines)
    union_count = 0
    words_list = ' '.join(contents_lines)\
                    .lower()\
                    .strip()\
                    .split()
    for index in range(len(words_list) -1 ):
        if  (words_list[index] == 'union' or words_list[index] == ')union'   ) and words_list[index + 1] != 'all'   :
            union_count += 1
    return union_count








#返回create table的次数
def get_create_table_count(line_list):
    contents_lines = line_list
    total_lines = ' '.join(contents_lines)
    create_table_count = 0
    words_list = ' '.join(contents_lines)\
                    .lower()\
                    .strip()\
                    .split()
    for index in range(len(words_list)):
        if index <  len(words_list) -2  and  words_list[index] == 'table' and words_list[index - 1].endswith('create') :
            create_table_count += 1
    return create_table_count


def get_word_count(line_list,keyword):
    contents_lines = line_list
    total_lines = ' '.join(contents_lines)
    word_count = 0
    words_list = ' '.join(contents_lines)\
                    .lower()\
                    .strip()\
                    .split()
    for index in range(len(words_list)):
        if words_list[index ] == keyword  or  words_list[index ] == ';' + keyword :
            word_count += 1
    return word_count


def tread_single_file(filepath):
    print 'start to reading new  file: ',filepath
    line_list = filtering_annotation(filepath)
    line_str_total = ' '.join(line_list)
    _count_dict = {}
    for key in _dict_ddl_weight :
        _count_dict[key] = get_word_count(line_list,key)
    for key in _dict_dml_weight :
        _count_dict[key] = get_word_count(line_list,key)
    _count_dict['create_view'] = get_create_view_count(line_list)
    _count_dict['create_table'] = get_create_table_count(line_list)
    _count_dict['view_name'] = get_view_name_count(line_list)
    _count_dict['with_name'] = get_with_table_names(line_list)
    _count_dict['union'] = get_union_count(line_list)
    _count_dict['unionall'] = get_unionAll_count(line_list)
    dml_weight = 0
    for key in _dict_dml_weight :
        dml_weight += _dict_dml_weight[key] * _count_dict[key]
    ddl_weight = 0
    for key in _dict_ddl_weight :
        ddl_weight += _dict_ddl_weight[key] * _count_dict[key]
    result_dict = _count_dict
    result_dict['dml_weight'] = dml_weight
    result_dict['ddl_weight'] = ddl_weight
    result_dict['total_weight'] = dml_weight + ddl_weight

    #print 'unionall: ',get_unionAll_count(line_list)
    #print 'union: ', get_union_count(line_list)


    return result_dict


def main(argv):
    inputfile = init(argv)
    result_dict_list = {}
    if os.path.isfile(inputfile):
        result_dict = tread_single_file(inputfile)
        result_dict_list[inputfile] = result_dict
    else :
        child_file_list = os.listdir(inputfile)
        for sfile in child_file_list:
            fpath = inputfile + '/' + sfile
            if os.path.isfile(fpath):
 		result_dict = tread_single_file(fpath)
                result_dict_list[fpath] = result_dict
    out_path = inputfile + '_result.csv'
    if os.path.exists(out_path):
    	os.remove(out_path) 
    result_out = open(out_path,'w')
    #write result to  out put path 
    print 'start writing result data to file with path : ' ,out_path
    resultOb = ResultObject(_nameList) 
    result_out.write(resultOb.get_filed_name() + '\n')
    result_out.write(resultOb.get_result_weight(_dict_ddl_weight,_dict_dml_weight) + '\n')
    for fpath in result_dict_list:
        result_out.write( resultOb.get_result_data(result_dict_list[fpath], fpath) + '\n' )
    result_out.close()

    



if __name__ == "__main__":
   main(sys.argv[1:])  

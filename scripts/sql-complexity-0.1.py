#!/usr/bin/env  python
# -*-  coding:utf-8 -*-

#
#权重以关键字操作的响应时间或者可能对任务产生性能瓶颈为基础，量化权重参考标准为：
#Schama操作一次为1；数据写入一次为5；一次Map操作为1；数据Exchange一次为5；排序一次为5；View重复调用一次为5；With子句重复调用一次为5.
#DDL权重表示了Sql脚本的结构性复杂度，DML权重表示了各子任务算子计算的复杂度；
#算法复杂度=DDL复杂度+DML复杂度;

"""

类别	关键字	权重	计算公式	备注
DDL	drop	1	总数*权重	
	create view	1	总数*权重	
	create table	5	总数*权重	
	alter	1	总数*权重	
	view_name	5	（总数-4）*权重	每张view的重复调用次数
	with_name	5	（总数-2）*权重	with子句按名称重复调用次数
	computer	2	总数*权重	
DML	select	1	总数*权重	一次map操作
	join	5	总数*权重	
	group	5	总数*权重	
	distinct	5	总数*权重	
	over	5	总数*权重	
	order	5	总数*权重	
	truncate	2	总数*权重	
	insert	5	总数*权重	
	union	5	总数*权重	
权重以关键字操作的响应时间或者可能对任务产生性能瓶颈为基础，量化权重参考标准为：Schama操作一次为1；数据写入一次为5；一次Map操作为1；数据Exchange一次为5；排序一次为5；View重复调用一次为5；With子句重复调用一次为5。				
				
				
"DDL权重表示了Sql脚本的结构性复杂度，DML权重表示了各子任务算子计算的复杂度；
算法复杂度=DDL复杂度+DML复杂度;"				
				
"""



import os,sys, getopt
import re

_dict_ddl_weight = {
  'drop' : 1,
  'create_view' : 1,
  'create_table' : 5,
  'alter' : 1,
  'computer' : 2,
  'view_name': 5,
  'with_name': 5
}


_dict_dml_weight = {
  'select' : 1,
  'join' : 5,
  'group' : 5,
  'distinct' : 5,
  'over' : 5,
  'order' : 5,
  'truncate' : 2,
  'insert' : 5,
  'union' : 5
}




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
   if ( os.path.isfile(inputfile)):
      return inputfile
   else :
      print inputfile + " is not a sql  file! "
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

    


def main(argv):
    inputfile = init(argv)
    print 'sql_name：', inputfile
    line_list = filtering_annotation(inputfile)
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
    for key in _count_dict:
        #print key ,' : ',_count_dict[key]
        pass
    dml_weight = 0
    for key in _dict_dml_weight :
        dml_weight += _dict_dml_weight[key] * _count_dict[key]
    ddl_weight = 0
    for key in _dict_ddl_weight :
        ddl_weight += _dict_ddl_weight[key] * _count_dict[key]
     
    print 'dml_weight: ',dml_weight
    print 'ddl_weight: ',ddl_weight
    print 'total_weight: ', dml_weight + ddl_weight 

if __name__ == "__main__":
   main(sys.argv[1:])  

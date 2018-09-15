# -*-  coding:utf-8 -*-


def read_single_file_2_lines(filepath):
    print('Reading from:' +filepath + '\n')
    file_object = open(filepath, 'r')
    contents = file_object.read()  # get contents from the path
    contents_lines = contents.split('\n')
    return contents_lines

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

    return with_name_count

#返回所有的view 名称以及该名称出现的次数
def  get_view_name_count(line_list):
    contents_lines = line_list
    with_name = get_with_table_names(contents_lines)
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
    return view_name_count


contents_lines = read_single_file_2_lines('demo.sql')
view_name_count = get_view_name_count(contents_lines)
with_name_count = get_with_table_names(contents_lines)
print view_name_count
print with_name_count



#print total_lines
#print with_name
#print "sql  analytics"

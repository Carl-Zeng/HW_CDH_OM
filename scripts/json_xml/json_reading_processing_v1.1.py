# -*- coding: utf-8 -*-
"""
Spyder Editor
Transfer Impala lineage log to gremlin queries.
"""

import json, os

def read_single_file(path):
    print('Reading: '+path+'\n')
    file_object = open(path,'r',encoding='UTF-8')
    contents = file_object.read()  #read contents     

    contents_list=contents.strip('\n').split('\n') #seperate contents into different json
    
    dict_list=[]
    #load each json
    for l in contents_list:
        dict_list.append(json.loads(l))

    file_object.close()
    #dict_list structure:
    #[dict1:{'queryText':string, 'hash':string, 'user':string, 'timestamp':int, 'endTime':int, 
    #'edges':[{'sources':[int, int ...], 'targets':[int, int ,...], 'edgeType':str},{},{}], 
    #'vertices':[{'id':int, 'vertexType':str, 'vertexId':"database.table.column"},{},{}]},
    #dict2:, dict3:, dict4:....]
        
    #one dict means one query or one lineage info
    return dict_list
  
    
'''
def get_tables_schema_and_columns(dict_list):
    table_list={}
    column_list=[]
    for d in dict_list:
        for v in d['vertices']:
            db_tb_col=v['vertexId'].split('.')
            db_tb=db_tb_col[0]+"."+db_tb_col[1]
            col=db_tb_col[2]
            #collect columbs
            column_list.append(db_tb_col)
            #collect table and columns for it
            if db_tb in table_list.keys():
                table_list[db_tb].append(col)
            else:
                table_list[db_tb]=[col]
    
    #remove redundant columbs
    column_list=list(set(column_list))
    
    #remove redundant columns in a table
    for t in table_list.keys():
        table_list[t]=list(set(table_list[t]))
    
    return table_list,column_list
'''

def get_table_column_name(ids):
    db_tb_col=ids.split('.')
    
    if len(db_tb_col)!=3:
        return False
    
    db_tb=db_tb_col[0]+"."+db_tb_col[1]
    col=db_tb_col[2]
    
    return [db_tb,col]


dict_list=[]

rootdir='D:\working\impala_lineage\logs'

list = os.listdir(rootdir) 
for i in range(0,len(list)):
       path = os.path.join(rootdir,list[i])
       if os.path.isfile(path):
           dict_list=read_single_file(path)+dict_list

#table_list,column_list=get_tables_schema_and_columns(dict_list)

print('reading finished\n')
print('Total read '+str(len(dict_list))+' records.\nProcessing begin!')

queries='graph = TinkerGraph.open()\n'
queries+='g = graph.traversal()\n'
queries+=':record start impala-lineage-log.txt\n'

table_column_list={} #{table_name:[column1,column2, ,,,]}
column_lineage_list={} #{column:[column1, column2, ,,,]}
table_lineage_list={} #{table_name:[table1, table2, ,,,]}

n_count=0
e_count=0

for d in dict_list:
    #create verteies for columns
    for v in d['vertices']:
        #split the database, table, column
        db_tb_col=get_table_column_name(v['vertexId'])
        
        #there must have three part in vertexId
        if not db_tb_col:
            continue
        
        #database.table
        db_tb=db_tb_col[0]
        #column
        col=db_tb_col[1]
                
        #collect table and columns info and their vertiex
        if db_tb in table_column_list.keys():
            if col not in table_column_list[db_tb]:
                table_column_list[db_tb].append(col)
                queries+='g.addV("'+v['vertexType']+'").property(id,"'+v['vertexId']+'").property("column_name","'+col+\
                '").property("table_belong","'+db_tb+'").next()\n'
                n_count+=1

        else:
            table_column_list[db_tb]=[col]
            #column vertiex
            queries+='g.addV("'+v['vertexType']+'").property(id,"'+v['vertexId']+'").property("column_name","'+col+\
            '").property("table_belong","'+db_tb+'").next()\n'
            n_count+=1
            
            #table vertiex
            queries+='g.addV("table").property(id,"'+db_tb+'").property("table_name","'+db_tb+'").next()\n'
            n_count+=1
    
    #create edge for column lineages
    for e in d['edges']:
        for source in e['sources']:
            db_tb_col=get_table_column_name(d['vertices'][source]['vertexId'])
            
            #there must have three part in vertexId
            if not db_tb_col:
                continue
            
            #database.table
            db_tb=db_tb_col[0]
            
            #create table lineage if parent table not exist
            if db_tb not in table_lineage_list.keys():
                table_lineage_list[db_tb]=[]
            
            #create column lineage if parent column not exist
            if d['vertices'][source]['vertexId'] not in column_lineage_list.keys():
                #new parent column found
                column_lineage_list[d['vertices'][source]['vertexId']]=[]
                for target in e['targets']:
                    db_tb_col_t=get_table_column_name(d['vertices'][target]['vertexId'])
                    
                    #there must have three part in vertexId
                    if not db_tb_col_t:
                        continue
                    #table name
                    db_tb_t=db_tb_col_t[0]
                    
                    #create table lineage if child table lineage is not exist
                    if db_tb_t not in table_lineage_list[db_tb]:
                        table_lineage_list[db_tb].append(db_tb_t)
                        
                    #create child column lineage
                    column_lineage_list[d['vertices'][source]['vertexId']].append(d['vertices'][target]['vertexId'])
                    
                    #set query
                    queries+='g.addE("column_parent").from(g.V("'+d['vertices'][source]['vertexId']+'")).to(g.V("'+\
                    d['vertices'][target]['vertexId']+'")).property("from_column","'+d['vertices'][source]['vertexId']+\
                    '").property("to_column","'+d['vertices'][target]['vertexId']+'").next()\n'
                    e_count+=1
                    
            else:
                #old parent column found
                for target in e['targets']:
                    db_tb_col_t=get_table_column_name(d['vertices'][target]['vertexId'])
                    #there must have three part in vertexId
                    if not db_tb_col_t:
                        continue
                    #table name
                    db_tb_t=db_tb_col_t[0]
                    
                    #create table lineage if child table lineage is not exist
                    if db_tb_t not in table_lineage_list[db_tb]:
                        table_lineage_list[db_tb].append(db_tb_t)
                        
                    #create column lineage if child column is not exist
                    if d['vertices'][target]['vertexId'] not in column_lineage_list[d['vertices'][source]['vertexId']]:
                        column_lineage_list[d['vertices'][source]['vertexId']].append(d['vertices'][target]['vertexId'])
                        
                        #set query
                        queries+='g.addE("column_parent").from(g.V("'+d['vertices'][source]['vertexId']+'")).to(g.V("'+\
                        d['vertices'][target]['vertexId']+'")).property("from_column","'+d['vertices'][source]['vertexId']+\
                        '").property("to_column","'+d['vertices'][target]['vertexId']+'").next()\n'
                        e_count+=1
                

for tf in table_lineage_list.keys():
    for tt in table_lineage_list[tf]:
        queries+='g.addE("table_parent").from(g.V("'+tf+'")).to(g.V("'+tt+'")).property("from_table","'+tf+\
        '").property("to_table","'+tt+'").next()\n'
        e_count+=1
        
for tf in table_column_list.keys():
    for colt in table_column_list[tf]:
        queries+='g.addE("column_of_table").from(g.V("'+tf+'")).to(g.V("'+tf+'.'+colt+'")).property(id,"'+tf+'_to_'+\
        colt+'").property("from_table","'+tf+'").property("to_column","'+colt+'").next()\n'
        e_count+=1
        
queries+=':record stop\n'
queries+=':remote connect tinkerpop.gephi\n'
queries+=':> graph\n'
f=open('D:\\working\\impala_lineage\\queries_str_id.txt','w')
f.write(queries)
f.close()
print('number of node: '+str(n_count))
print('number of edge: '+str(e_count))

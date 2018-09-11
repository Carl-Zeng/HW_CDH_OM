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

queries='<?xml version="1.0" ?><graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="'+\
'http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns'+\
' http://graphml.graphdrawing.org/xmlns/1.1/graphml.xsd"><key id="labelV" for="node" attr.name="labelV"'+\
' attr.type="string"></key><key id="table_belong" for="node" attr.name="table_belong" attr.type="string">'+\
'</key><key id="column_name" for="node" attr.name="column_name" attr.type="string"></key>'+\
'<key id="table_name" for="node" attr.name="table_name" attr.type="string"></key><key id="labelE" '+\
'for="edge" attr.name="labelE" attr.type="string"></key>'+\
'<key id="from_table" for="edge" attr.name="from_table" attr.type="string" />'+\
'<key id="to_table" for="edge" attr.name="to_table" attr.type="string" /><key id="to_column" for="edge"'+\
' attr.name="to_column" attr.type="string" /><key id="from_column" for="edge" attr.name="from_column"'+\
' attr.type="string" /><graph id="G" edgedefault="directed">'

table_column_list={} #{table_name:[column1,column2, ,,,]}
column_lineage_list={} #{column:[column1, column2, ,,,]}
table_lineage_list={} #{table_name:[table1, table2, ,,,]}

id=1

dict_id={} #for recorde the relationship between id and name

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
                queries+='<node id="'+str(id)+'"><data key="labelV">'+v['vertexType']+'</data><data key="column_name">'+col+\
                '</data><data key="table_belong">'+db_tb+'</data></node>'
                dict_id[v['vertexId']]=id
                id+=1

        else:
            table_column_list[db_tb]=[col]
            #column vertiex
            queries+='<node id="'+str(id)+'"><data key="labelV">'+v['vertexType']+'</data><data key="column_name">'+col+\
            '</data><data key="table_belong">'+db_tb+'</data></node>'
            dict_id[v['vertexId']]=id
            id+=1
            
            #table vertiex
            queries+='<node id="'+str(id)+'"><data key="labelV">table</data><data key="table_name">'+db_tb+'</data></node>'
            dict_id[db_tb]=id
            id+=1
    
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
                    queries+='<edge id="'+str(id)+'" source="'+str(dict_id[d['vertices'][source]['vertexId']])+\
                    '" target="'+str(dict_id[d['vertices'][target]['vertexId']])+'"><data key="labelE">column_parent</data><data key="from_column">'+\
                    d['vertices'][source]['vertexId']+'</data><data key="to_column">'+d['vertices'][target]['vertexId']+'</data></edge>'
                    id+=1
            
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
                        queries+='<edge id="'+str(id)+'" source="'+str(dict_id[d['vertices'][source]['vertexId']])+\
                        '" target="'+str(dict_id[d['vertices'][target]['vertexId']])+'"><data key="labelE">column_parent</data><data key="from_column">'+\
                        d['vertices'][source]['vertexId']+'</data><data key="to_column">'+d['vertices'][target]['vertexId']+'</data></edge>'
                        id+=1
                        
                

for tf in table_lineage_list.keys():
    for tt in table_lineage_list[tf]:
        queries+='<edge id="'+str(id)+'" source="'+str(dict_id[tf])+'" target="'+str(dict_id[tt])+\
        '"><data key="labelE">table_parent</data><data key="from_table">'+\
        tf+'</data><data key="to_table">'+tt+'</data></edge>'
        id+=1
        
for tf in table_column_list.keys():
    for colt in table_column_list[tf]:
        queries+='<edge id="'+str(id)+'" source="'+str(dict_id[tf])+'" target="'+str(dict_id[tf+'.'+colt])+'">'+\
        '<data key="labelE">table_column</data><data key="from_table">'+\
        tf+'</data><data key="to_column">'+tf+'.'+colt+'</data></edge>'
        id+=1
       
queries+='</graph></graphml>'
f=open('D:\\working\\impala_lineage\\graph_data_int_id.xml','w')
f.write(queries)
f.close()

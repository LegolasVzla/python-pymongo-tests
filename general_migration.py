#!/usr/bin/python3
from databases_connection import *
import psycopg2, psycopg2.extras
import json
import datetime
#from pprint import pprint
#pprint(x)

def mongo_collections_list(monCli,monDB):
	# Generic method to get and list all the mongodb collections
	collections = dict((monDB, [collection for collection in monCli[monDB].collection_names(include_system_collections=False)])
		for monDB in monCli.database_names())
	return collections

def postgres_query_load(pgcon,pgcur,data,query):
	# Generic method to load data in postgres tables
	pgcur.execute(query)
	pgcon.commit()

def postgres_json_export_to_file(pgcon,pgcur,query,filename):
	# Generic method to generate json data files
	pgcur.execute(query)
	json_data = pgcur.fetchall()[0]
	#print (json_data)
	if(len(json_data)!=0):
		file=open(filename+".json",'w')
		file.write(str(json_data[0]))

def main():
	monCli, monDB = mongoConnection()
	pgcon, pgcur = postgresConnection()	

	original_path = os.getcwd()	
	#os.chdir(original_path+"/db/seeders")

	pgcon.close()
	pgcur.close()	

if __name__ == '__main__':
    main()

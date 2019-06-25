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

def mongo_user_extraction(monCli,monDB,pgcon,pgcur):
	collections = mongo_collections_list(monCli,monDB)
	user_collection_name = collections['ibeentest'][1]
	user_collection_data = monDB[user_collection_name]
	query = ""
	#x = user_collection_data.find_one()
	# Get all the user data
	for i,data in enumerate(user_collection_data.find()):
		if(i >1):

			# Missing SQL inject prevention using: VALUES (%,%..) and pgcur.execute(query,(var,var..))
			query = "INSERT INTO users (email,status_account,created_at,updated_at) VALUES ('"+data['email']['value']+"',0,'"+data['createdOn']['instant'].isoformat()+"',now())"
			# for each mongo user document, insert in postgres user table
			postgres_query_load(pgcon,pgcur,data,query)
			#time.sleep(5)
			# pprint(data)

	query = "SELECT json_agg(a.*) FROM (SELECT id, email, status_account, created_at, updated_at, is_active, is_deleted FROM users) a"
	filename = "user"

	# Generate json user data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

def mongo_friends_extraction(monCli,monDB,pgcon,pgcur):
	query = ""
	user_id = None
	friend_id = None
	full_user_name = ""
	pgcur.execute("SELECT id,email FROM users")
	json_data_users = pgcur.fetchall()

	# Get all the friendships data
	for i in monDB.friends.find():
		# Search for the user id of the user
		for j in json_data_users:
			if i['user']['_id'] == j[1]:
				user_id=j[0]
				full_user_name=i['user']['fullname']
		# Search for the friend id
		for j in json_data_users:
			if i['friend']['_id'] == j[1]:
				friend_id=j[0]

		# Missing SQL inject prevention using: VALUES (%,%..) and pgcur.execute(query,(var,var..))
		query = "INSERT INTO friendships (friend_id,friendable_id,status,created_at,updated_at) VALUES ("+str(user_id)+","+str(friend_id)+",2,'"+i['createdAt'].isoformat()+"',now())"

		# For each mongo friendships document, insert in postgres friendships table
		postgres_query_load(pgcon,pgcur,i,query)

		# Add the fullname to the users
		pgcur.execute("UPDATE users SET first_name = '"+full_user_name+"' WHERE id="+str(user_id))

	query = "SELECT json_agg(a.*) FROM (SELECT id, friend_id, friendable_id, status,created_at, updated_at,is_active,is_deleted FROM friendships) a"
	filename = "friendships"

	# Generate json friendships data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

def mongo_tags_extraction(monCli,monDB,pgcon,pgcur):
	query = ""
	tag_name = ""
	user_id = None
	tag_id = ""
	pgcur.execute("SELECT id,email FROM users")
	json_data_users = pgcur.fetchall()

	# Get all the friendships data
	for i in monDB.tags.find():
		# Search for the user id of the user
		for j in json_data_users:
			if i['author'] == j[1]:
				user_id=j[0]
				tag_name=i['_id']

		# Missing SQL inject prevention using: VALUES (%,%..) and pgcur.execute(query,(var,var..))
		query = "INSERT INTO tags (name) VALUES ('"+tag_name+"') RETURNING id"

		# For each mongo tags document, insert in postgres tags table
		postgres_query_load(pgcon,pgcur,i,query)

		tag_id = pgcur.fetchone()[0]

		# Missing SQL inject prevention using: VALUES (%,%..) and pgcur.execute(query,(var,var..))
		query = "INSERT INTO spots_tags (spot_users_id,tags_id) VALUES ("+str(user_id)+","+str(tag_id)+")"

		# Generate the relationship spot_tags data
		postgres_query_load(pgcon,pgcur,i,query)

	query = "SELECT json_agg(a.*) FROM (SELECT id,name,created_at,updated_at,is_active,is_deleted FROM tags) a"
	filename = "tags"

	# Generate json tags data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	query = "SELECT json_agg(a.*) FROM (SELECT id,spot_users_id,tags_id,created_at,updated_at,is_active,is_deleted FROM spots_tags) a"
	filename = "spots_tags"

	# Generate json spots_tags data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

def main():
	monCli, monDB = mongoConnection()
	pgcon, pgcur = postgresConnection()	

	original_path = os.getcwd()	
	#os.chdir(original_path+"/db/seeders")
	mongo_user_extraction(monCli,monDB,pgcon,pgcur)
	mongo_friends_extraction(monCli,monDB,pgcon,pgcur)
	mongo_tags_extraction(monCli,monDB,pgcon,pgcur)
	
	pgcon.close()
	pgcur.close()	

if __name__ == '__main__':
    main()

#!/usr/bin/python3
from databases_connection import *
import psycopg2, psycopg2.extras
import json
import datetime
#import time
#from pprint import pprint
#pprint(x)

def mongo_collections_list(monCli,monDB):
	# get and list all the mongodb collections
	collections = dict((monDB, [collection for collection in monCli[monDB].collection_names(include_system_collections=False)])
		for monDB in monCli.database_names())
	return collections

def postgres_query_load(pgcon,pgcur,data,query):
	# Load data in the postgres user table
	pgcur.execute(query)
	pgcon.commit()

def postgres_json_export_to_file(pgcon,pgcur,query,filename):
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
			query = "INSERT INTO users (email,status_account,created_at,updated_at) VALUES ('"+data['email']['value']+"',0,'"+data['createdOn']['instant'].isoformat()+"',now())"
			# for each mongo user document, insert in postgres user table
			postgres_query_load(pgcon,pgcur,data,query)
			#time.sleep(5)
			# pprint(data)

	# Generate all the seeders needed
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
		# Search for the user_id of the user by email comparison
		for j in json_data_users:
			if i['user']['_id'] == j[1]:
				user_id=j[0]
				full_user_name=i['user']['fullname']
		# Search for the friend id
		for j in json_data_users:
			if i['friend']['_id'] == j[1]:
				friend_id=j[0]

		query = "INSERT INTO friendships (friend_id,friendable_id,status,created_at,updated_at) VALUES ("+str(user_id)+","+str(friend_id)+",2,'"+i['createdAt'].isoformat()+"',now())"

		# For each mongo friendships document, insert in postgres friendships table
		postgres_query_load(pgcon,pgcur,i,query)

		# Add the fullname to the users
		pgcur.execute("UPDATE users SET first_name = '"+full_user_name+"' WHERE id="+str(user_id))

	# Generate all the seeders needed
	query = "SELECT json_agg(a.*) FROM (SELECT id, friend_id, friendable_id, status,created_at, updated_at,is_active,is_deleted FROM friendships) a"
	filename = "friendships"

	# Generate json friendships data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

def mongo_tags_extraction(monCli,monDB,pgcon,pgcur):
	query = ""
	tag_name = ""
	user_id = None
	tag_id = None
	pgcur.execute("SELECT id,email FROM users")
	json_data_users = pgcur.fetchall()

	# Get all the friendships data
	for i in monDB.tags.find():
		# Search for the user_id of the user by email comparison
		for j in json_data_users:
			if i['author'] == j[1]:
				user_id=j[0]
				tag_name=i['_id']

		query = "INSERT INTO tags (name) VALUES ('"+tag_name+"') RETURNING id"

		# For each mongo tags document, insert in postgres tags table
		postgres_query_load(pgcon,pgcur,i,query)

		tag_id = pgcur.fetchone()[0]

		query = "INSERT INTO spots_tags (spot_users_id,tags_id) VALUES ("+str(user_id)+","+str(tag_id)+")"

		# Generate the relationship spot_tags data
		postgres_query_load(pgcon,pgcur,i,query)

	# Generate all the seeders needed
	query = "SELECT json_agg(a.*) FROM (SELECT id,name,created_at,updated_at,is_active,is_deleted FROM tags) a"
	filename = "tags"

	# Generate json tags data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	query = "SELECT json_agg(a.*) FROM (SELECT id,spot_users_id,tags_id,created_at,updated_at,is_active,is_deleted FROM spots_tags) a"
	filename = "spots_tags"

	# Generate json spots_tags data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

def mongo_spots_extraction(monCli,monDB,pgcon,pgcur):
	query = ""
	user_id = None
	category_id = None
	tag_name = None
	tag_id = None
	tag_validator = False
	spot_id = None
	spots_tags_id = None
	status_id = None
	review = None
	remarks = None
	is_privated = False
	pgcur.execute("SELECT id,email FROM users")
	json_data_users = pgcur.fetchall()

	pgcur.execute("SELECT id,name FROM category")
	json_data_category = pgcur.fetchall()

	pgcur.execute("SELECT id,name FROM tags")
	json_data_tags = pgcur.fetchall()

	# Get all the spots data
	for i in monDB.spots.find():
		# Searching the user_id of the user by email comparison
		for j in json_data_users:
			if i['user']['_id'] == j[1]:
				user_id=j[0]

		# Searching the category_id of the spot category name comparison
		for j in json_data_category:
			if i['categoryId'] == j[1]:
				category_id=j[0]

		# For each tags list, search for the tag_id category name comparison
		for j in i['tags']:
			for k in json_data_tags:
				# If the tags names are equals, get the tag_id
				if j[1] == k:
					tag_id=k[0]
					tag_validator = True
			# New tag found
			if not tag_validator:
				query = "INSERT INTO tags (name,created_at,updated_at) VALUES ('"+i['tags'][j]+"','"+i['createdAt'].isoformat()+"',now()) RETURNING id"

				# Insert the new tag
				postgres_query_load(pgcon,pgcur,i,query)

				tag_id = pgcur.fetchone()[0]

			query = "INSERT INTO spots_tags (user_id,tags_id,created_at,updated_at) VALUES ("+str(user_id)+","+str(tag_id)+",'"+i['createdAt'].isoformat()+"',now()) RETURNING id"

			# Insert the current spots_tags
			postgres_query_load(pgcon,pgcur,i,query)

			spots_tags_id = pgcur.fetchone()[0]

			query = "INSERT INTO user_actions (entity_action_id,types_user_actions_id,created_at) VALUES ("+str(spots_tags_id)+","+str(2)+",'"+i['createdAt'].isoformat()+"')"

			# Insert the user_actions
			postgres_query_load(pgcon,pgcur,i,query)

		query = "INSERT INTO spots (name,created_at,updated_at) VALUES ('"+i['title']+"','"+i['createdAt'].isoformat()+"',now()) RETURNING id"

		# Insert the current spot
		postgres_query_load(pgcon,pgcur,i,query)

		spot_id = pgcur.fetchone()[0]

		# Check if the spots has review value
		try:
			review = i['review']
		except Exception as e:
			review = None

		# Check if the spots has remarks value
		try:
			remarks = i['remarks']
		except Exception as e:
			remarks = None

		# Check the status and the privacity of the spot
		if(i['status'] == "published"):
			status_id = 5	# Activo
		elif(i['status'] == "draft"):
			is_privated = True
			status_id = 5	# Activo
		else:
			print ("New Status:",i['status'])
			#time.sleep(3)

		query = "INSERT INTO user_actions (entity_action_id,types_user_actions_id,created_at) VALUES ("+str(spot_id)+","+str(1)+",'"+i['createdAt'].isoformat()+"')"

		# Insert the user_actions
		postgres_query_load(pgcon,pgcur,i,query)

		# Insert the spot_users data
		query = "INSERT INTO spot_users (user_id,spot_id,review,remarks,status_id,is_privated,created_at,updated_at) VALUES ("+str(user_id)+","+str(spot_id)+",'"+review+"','"+remarks+"',"+str(status_id)+","+str(is_privated)+",'"+i['createdAt'].isoformat()+"',now()) RETURNING id"

		postgres_query_load(pgcon,pgcur,i,query)

		spot_users_id = pgcur.fetchone()[0]

		query = "INSERT INTO spot_categories (spot_users_id,categories_id,created_at,updated_at) VALUES ("+str(spot_users_id)+","+str(category_id)+",'"+i['createdAt'].isoformat()+"',now())"

		# Insert the spot_categories data
		postgres_query_load(pgcon,pgcur,i,query)				

		# For each gallery, iterates over all images
		for j in (i['gallery']):
			# For each image of the current spot, insert them
			for k in (j['images']):

				query = "INSERT INTO site_images (spot_id,uri,extension,principalImage,original,created_at,updated_at) VALUES ("+str(spot_id)+",'"+k['uri']+"','"+j['extension']+"',"+str(j['principalImage'])+",'"+k['type']+"','"+j['created'].isoformat()+"',now())"

				# Insert the data image
				postgres_query_load(pgcon,pgcur,i,query)

	# Generate all the seeders needed
	query = "SELECT json_agg(a.*) FROM (SELECT id,name,review,remarks,status_id,created_at,updated_at,is_active,is_deleted FROM spots) a"
	filename = "spots"

	# Generate json spots data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	query = "SELECT json_agg(a.*) FROM (SELECT id,spot_id,uri,extension,original,principalimage,created_at,updated_at,is_active,is_deleted FROM site_images) a"
	filename =  "site_images"

	# Generate json site_images data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	query = "SELECT json_agg(a.*) FROM (SELECT id,user_id,spot_id,is_privated,created_at,updated_at,is_active,is_deleted FROM spot_users) a"
	filename = "spot_users"

	# Generate json spot_users data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	query = "SELECT json_agg(a.*) FROM (SELECT id,spot_users,categories,created_at,updated_at,is_active,is_deleted FROM spot_categories) a"
	filename =  "spot_categories"

	# Generate json spot_categories data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

def main():
	monCli, monDB = mongoConnection()
	pgcon, pgcur = postgresConnection()	

	original_path = os.getcwd()
	#os.chdir(original_path+"/db/seeders")
	mongo_user_extraction(monCli,monDB,pgcon,pgcur)
	mongo_friends_extraction(monCli,monDB,pgcon,pgcur)
	mongo_tags_extraction(monCli,monDB,pgcon,pgcur)
	#mongo_spots_extraction(monCli,monDB,pgcon,pgcur)

	pgcon.close()
	pgcur.close()	

if __name__ == '__main__':
    main()

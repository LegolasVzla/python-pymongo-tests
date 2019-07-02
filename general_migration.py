#!/usr/bin/python3
from databases_connection import *
import psycopg2, psycopg2.extras
import json
import datetime
import time
#from pprint import pprint
#pprint(x)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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
	first_name = ""
	last_name = ""
	#x = user_collection_data.find_one()
	# Get all the user data
	for i,user_data in enumerate(user_collection_data.find()):
		if(i >1):
			query = "INSERT INTO users (first_name,last_name,email,status_account,created_at,updated_at) VALUES ('"+first_name+"','"+last_name+"','"+user_data['email']['value']+"',0,'"+user_data['createdOn']['instant'].isoformat()+"',now())"
			# for each mongo user document, insert in postgres user table
			postgres_query_load(pgcon,pgcur,user_data,query)
			#time.sleep(5)
			# pprint(data)
			print (bcolors.OKBLUE + "Executing User data migration. Row: "+ str(i) + bcolors.ENDC)

	# This part will be overwritten in spot migration
	# Generate all the seeders needed
	'''
	query = "SELECT json_agg(a.*) FROM (SELECT id, email, status_account, created_at, updated_at, is_active, is_deleted FROM users) a"
	filename = "user"

	# Generate json user data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)
	'''

def mongo_friends_extraction(monCli,monDB,pgcon,pgcur):
	query = ""
	user_id = None
	friend_id = None
	full_user_name = ""
	first_name = ""
	last_name = ""
	pgcur.execute("SELECT id,email FROM users")
	json_data_users = pgcur.fetchall()

	# Get all the friendships data
	for i,friends_data in enumerate(monDB.friends.find()):
		# Search for the user_id of the user by email comparison
		for j in json_data_users:
			if friends_data['user']['_id'] == j[1]:
				user_id=j[0]
				full_user_name=friends_data['user']['fullname']
		# Search for the friend id
		for j in json_data_users:
			if friends_data['friend']['_id'] == j[1]:
				friend_id=j[0]

		query = "INSERT INTO friendships (friend_id,friendable_id,status,created_at,updated_at) VALUES ("+str(user_id)+","+str(friend_id)+",2,'"+friends_data['createdAt'].isoformat()+"',now())"

		# For each mongo friendships document, insert in postgres friendships table
		postgres_query_load(pgcon,pgcur,friends_data,query)

		if(len(full_user_name.split(' ')) == 2):
			first_name = full_user_name.split(' ')[0]
			last_name = full_user_name.split(' ')[1]
		elif(len(full_user_name.split(' ')) == 3):
			first_name = full_user_name.split(' ')[0] + " " + full_user_name.split(' ')[1]
			last_name = full_user_name.split(' ')[2]
		elif(len(full_user_name.split(' ')) == 4):
			first_name = full_user_name.split(' ')[0] + " " + full_user_name.split(' ')[1]
			last_name = full_user_name.split(' ')[2] + " " + full_user_name.split(' ')[3]

		# Add the first_name and last_name to the users
		pgcur.execute("UPDATE users SET first_name = '"+first_name+"', last_name = '"+last_name+"' WHERE id="+str(user_id))

		print (bcolors.OKBLUE + "Executing Friendships data migration. Row: "+ str(i) + bcolors.ENDC)

	# Generate all the seeders needed
	query = "SELECT json_agg(a.*) FROM (SELECT id,friend_id,friendable_id,status,created_at, updated_at,is_active,is_deleted FROM friendships) a"
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
	for i,tags_data in enumerate(monDB.tags.find()):
		# Search for the user_id of the user by email comparison
		for j in json_data_users:
			if tags_data['author'] == j[1]:
				user_id=j[0]
				tag_name=tags_data['_id']

		query = "INSERT INTO tags (name) VALUES ('"+tag_name+"') RETURNING id"

		# For each mongo tags document, insert in postgres tags table
		postgres_query_load(pgcon,pgcur,i,query)

		tag_id = pgcur.fetchone()[0]

		query = "INSERT INTO spots_tags (user_id,tags_id) VALUES ("+str(user_id)+","+str(tag_id)+")"

		# Generate the relationship spot_tags data
		postgres_query_load(pgcon,pgcur,i,query)

		print (bcolors.OKBLUE + "Executing Tags data migration. Row: "+ str(i) + bcolors.ENDC)

	# Generate all the seeders needed
	query = "SELECT json_agg(a.*) FROM (SELECT id,name,created_at,updated_at,is_active,is_deleted FROM tags) a"
	filename = "tags"

	# Generate json tags data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	query = "SELECT json_agg(a.*) FROM (SELECT id,user_id,tags_id,created_at,updated_at,is_active,is_deleted FROM spots_tags) a"
	filename = "spots_tags"

	# Generate json spots_tags data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

def mongo_spots_extraction(monCli,monDB,pgcon,pgcur):
	query = ""
	user_id = None
	full_user_name = ""
	category_id = None
	tag_name = None
	tag_id = None
	spot_id = None
	spots_tags_id = None
	status_id = None
	review = None
	remarks = None
	spot_name = None
	is_privated = False
	pgcur.execute("SELECT id,email FROM users")
	json_data_users = pgcur.fetchall()

	pgcur.execute("SELECT id,name FROM category")
	json_data_category = pgcur.fetchall()

	pgcur.execute("SELECT id,name FROM tags")
	json_data_tags = pgcur.fetchall()

	# Get all the spots data
	for i,spot_data in enumerate(monDB.spots.find()):
		# Searching the user_id of the user by email comparison
		for j in json_data_users:
			if spot_data['user']['_id'] == j[1]:
				user_id=j[0]

		# Searching the category_id of the spot category name comparison
		for j in json_data_category:
			if spot_data['categoryId'] == j[1]:
				category_id=j[0]

		# If there almost one tag
		if(len(spot_data['tags'])>0):

			# For each tags list, search for the tag_id category name comparison
			for j in spot_data['tags']:

				tag_validator = False
				
				for k in json_data_tags:

					# If the tags names are equals, get the tag_id
					if j == k[1]:
						tag_id=k[0]
						tag_validator = True
				# New tag found
				if not tag_validator:

					print (bcolors.WARNING + "New Tag found: "+ str(j) + bcolors.ENDC)
					#time.sleep(1)

					query = "INSERT INTO tags (name,created_at,updated_at) VALUES ('"+j+"','"+spot_data['createdAt'].isoformat()+"',now()) RETURNING id"

					# Insert the new tag
					postgres_query_load(pgcon,pgcur,i,query)

					tag_id = pgcur.fetchone()[0]

				query = "INSERT INTO spots_tags (user_id,tags_id,created_at,updated_at) VALUES ("+str(user_id)+","+str(tag_id)+",'"+spot_data['createdAt'].isoformat()+"',now()) RETURNING id"

				# Insert the current spots_tags
				postgres_query_load(pgcon,pgcur,i,query)

				spots_tags_id = pgcur.fetchone()[0]

				# Reload the tags query
				pgcur.execute("SELECT id,name FROM tags")
				json_data_tags = pgcur.fetchall()

				query = "INSERT INTO user_actions (entity_action_id,types_user_actions_id,created_at) VALUES ("+str(spots_tags_id)+","+str(2)+",'"+spot_data['createdAt'].isoformat()+"')"

				# Insert the user_actions
				postgres_query_load(pgcon,pgcur,i,query)

		# Add missing fullnames to the users
		if(len(spot_data['user']['fullname'].split(' ')) == 2):
			first_name = spot_data['user']['fullname'].split(' ')[0]
			last_name = spot_data['user']['fullname'].split(' ')[1]
		elif(len(spot_data['user']['fullname'].split(' ')) == 3):
			first_name = spot_data['user']['fullname'].split(' ')[0] + " " + spot_data['user']['fullname'].split(' ')[1]
			last_name = spot_data['user']['fullname'].split(' ')[2]
		elif(len(spot_data['user']['fullname'].split(' ')) == 4):
			first_name = spot_data['user']['fullname'].split(' ')[0] + " " + spot_data['user']['fullname'].split(' ')[1]
			last_name = spot_data['user']['fullname'].split(' ')[2] + " " + spot_data['user']['fullname'].split(' ')[3]

		# Add the first_name and last_name to the users
		pgcur.execute("UPDATE users SET first_name = '"+first_name+"', last_name = '"+last_name+"' WHERE id="+str(user_id))

		# Check if the spots has review value
		try:
			review = spot_data['review']
		except Exception as e:
			review = None

		# Check if the spots has remarks value
		try:
			remarks = spot_data['remarks']
		except Exception as e:
			remarks = None

		# Check the status and the privacity of the spot
		if(spot_data['status'] == "published"):
			status_id = 5	# Activo
		elif(spot_data['status'] == "draft"):
			is_privated = True
			status_id = 5	# Activo
		else:
			print (bcolors.WARNING + "New Spot Status: "+ spot_data['status'] + bcolors.ENDC)
			#time.sleep(1)

		spot_name = spot_data['title'].replace("'",'`')

		# HERE will be the PoSTGis geolocalization translate code

		query = "INSERT INTO spots (user_id,name,review,remarks,status_id,is_privated,lat,long,created_at,updated_at) VALUES ("+str(user_id)+",'"+spot_name+"','"+str(review)+"','"+str(remarks)+"',"+str(status_id)+","+str(is_privated)+","+str(spot_data['place']['point']['coordinates'][0])+","+str(spot_data['place']['point']['coordinates'][1])+",'"+spot_data['createdAt'].isoformat()+"',now()) RETURNING id"

		print (bcolors.OKBLUE + "Executing Spots data migration. Row: "+ str(i) + bcolors.ENDC)

		# Insert the current spot
		postgres_query_load(pgcon,pgcur,i,query)

		spot_id = pgcur.fetchone()[0]

		query = "INSERT INTO user_actions (entity_action_id,types_user_actions_id,created_at) VALUES ("+str(spot_id)+","+str(1)+",'"+spot_data['createdAt'].isoformat()+"')"

		print (bcolors.OKBLUE + "Executing User_actions data migration. Row: "+ str(i) + bcolors.ENDC)

		# Insert the user_actions
		postgres_query_load(pgcon,pgcur,i,query)

		# Insert the spot_users data
		#query = "INSERT INTO spot_users (user_id,spot_id,review,remarks,status_id,is_privated,created_at,updated_at) VALUES ("+str(user_id)+","+str(spot_id)+",'"+str(review)+"','"+str(remarks)+"',"+str(status_id)+","+str(is_privated)+",'"+spot_data['createdAt'].isoformat()+"',now()) RETURNING id"

		#postgres_query_load(pgcon,pgcur,i,query)

		#print (bcolors.OKBLUE + "Executing Spots_users data migration. Row: "+ str(i) + bcolors.ENDC)

		#spot_users_id = pgcur.fetchone()[0]

		query = "INSERT INTO spot_categories (spot_id,categories_id,created_at,updated_at) VALUES ("+str(spot_id)+","+str(category_id)+",'"+spot_data['createdAt'].isoformat()+"',now())"

		print (bcolors.OKBLUE + "Executing Spots_categories data migration. Row: "+ str(i) + bcolors.ENDC)

		# Insert the spot_categories data
		postgres_query_load(pgcon,pgcur,i,query)				

		# For each gallery, iterates over all images
		for j,gallery_data in enumerate(spot_data['gallery']):

			query = "INSERT INTO site_images (spot_id,uri,extension,principalImage,original,created_at,updated_at) VALUES ("+str(spot_id)+",'"+gallery_data['images']['uri']+"','"+gallery_data['extension']+"','"+str(gallery_data['principalImage'])+"','"+gallery_data['images']['type']+"','"+gallery_data['created'].isoformat()+"',now())"

			print (bcolors.OKBLUE + "Executing Site_Images data migration. Row: "+ str(j) + " of the Spot row: " + str(i) + " iteration" + bcolors.ENDC)

			# Insert the data image
			postgres_query_load(pgcon,pgcur,i,query)

	print (bcolors.OKBLUE + "Generating user_actions, spots, site_images and spot_categories seeders"+ bcolors.ENDC)

	# Generate all the seeders needed
	query = "SELECT json_agg(a.*) FROM (SELECT id, email, status_account, created_at, updated_at, is_active, is_deleted FROM users) a"
	filename = "user"

	# Generate json user data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	query = "SELECT json_agg(a.*) FROM (SELECT id,entity_action_id,types_user_actions_id,created_at,is_active,is_deleted FROM user_actions) a"
	filename = "user_actions"

	# Generate json user_actions data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	# Generate all the seeders needed
	query = "SELECT json_agg(a.*) FROM (SELECT id,name,lat,long,created_at,updated_at,is_active,is_deleted FROM spots) a"
	filename = "spots"

	# Generate json spots data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	query = "SELECT json_agg(a.*) FROM (SELECT id,spot_id,uri,extension,original,principalimage,created_at,updated_at,is_active,is_deleted FROM site_images) a"
	filename =  "site_images"

	# Generate json site_images data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	#query = "SELECT json_agg(a.*) FROM (SELECT id,user_id,spot_id,is_privated,review,remarks,status_id,created_at,updated_at,is_active,is_deleted FROM spot_users) a"
	#filename = "spot_users"

	# Generate json spot_users data
	#postgres_json_export_to_file(pgcon,pgcur,query,filename)

	query = "SELECT json_agg(a.*) FROM (SELECT id,spot_id,categories_id,created_at,updated_at,is_active,is_deleted FROM spot_categories) a"
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
	mongo_spots_extraction(monCli,monDB,pgcon,pgcur)

	pgcon.close()
	pgcur.close()	

if __name__ == '__main__':
    main()

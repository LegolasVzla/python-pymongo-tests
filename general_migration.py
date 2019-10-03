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
			query = "INSERT INTO users (first_name,last_name,full_name,email,status_account,created_at,updated_at) VALUES ('"+first_name+"','"+last_name+"','"+first_name+"' '"+last_name+"', '"+user_data['email']['value']+"',1,'"+user_data['createdOn']['instant'].isoformat()+"',now())"
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

		query = "INSERT INTO friendships (friend_id,friendable_type,friendable_id,status,created_at,updated_at) VALUES ("+str(user_id)+",'User',"+str(friend_id)+",2,'"+friends_data['createdAt'].isoformat()+"',now())"

		# For each mongo friendships document, insert in postgres friendships table the first relationship: A is friend of B
		postgres_query_load(pgcon,pgcur,friends_data,query)

		query = "INSERT INTO friendships (friend_id,friendable_type,friendable_id,status,created_at,updated_at) VALUES ("+str(user_id)+",'User',"+str(friend_id)+",2,'"+friends_data['createdAt'].isoformat()+"',now())"

		# For each mongo friendships document, insert in postgres friendships table the second relationship: B is friend of A
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

	print (bcolors.OKBLUE + "Generating friendships seeder"+ bcolors.ENDC)

	# Generate all the seeders needed
	query = "SELECT json_agg(a.*) FROM (SELECT id,friend_id,friendable_id,status,created_at, updated_at,is_active,is_deleted FROM friendships) a"
	filename = "friendships"

	# Generate json friendships data
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
	place_name = None
	spot_name = None
	is_privated = False
	country_name = None
	city_name = None
	state_name = None
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

			# For each tags list, search for the tag_id and compare them by name
			for j in spot_data['tags']:

				tag_validator = False
				
				# Compare with the tags that are already stored in the tags table
				for k in json_data_tags:

					# If the tags names are equals, get the tag_id
					if j == k[1]:
						tag_id=k[0]
						tag_validator = True

				# Tag not found in the tags table, so it's a New tag
				if not tag_validator:

					print (bcolors.WARNING + "New Tag found: "+ str(j) + bcolors.ENDC)
					#time.sleep(1)

					query = "INSERT INTO tags (name,created_at,updated_at) VALUES ('"+j+"','"+spot_data['createdAt'].isoformat()+"',now()) RETURNING id"

					# Insert the new tag
					postgres_query_load(pgcon,pgcur,i,query)

					tag_id = pgcur.fetchone()[0]

				#-------------------------------------
				# Here will be the user action code related with spot tags
				#-------------------------------------

				# In any case (tag already exist or new tag) insert a new spot_tag with the current tag_id
				query = "INSERT INTO spot_tags (user_id,tags_id,created_at,updated_at) VALUES ("+str(user_id)+","+str(tag_id)+",'"+spot_data['createdAt'].isoformat()+"',now()) RETURNING id"

				# Insert the current spots_tags
				postgres_query_load(pgcon,pgcur,i,query)

				spots_tags_id = pgcur.fetchone()[0]

				# Reload the tags query
				pgcur.execute("SELECT id,name FROM tags")
				json_data_tags = pgcur.fetchall()

				'''
				query = "INSERT INTO user_actions (entity_action_id,types_user_actions_id,created_at) VALUES ("+str(spots_tags_id)+","+str(2)+",'"+spot_data['createdAt'].isoformat()+"')"

				# Insert the user_actions
				postgres_query_load(pgcon,pgcur,i,query)
				'''

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

		# Add the first_name and last_name to the users with missing first and last name
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

		# Check if the spots has name value
		try:
			place_name = spot_data['place']['name'].replace("'",'`')
		except Exception as e:
			place_name = None

		# Check if the spots has cityName value
		try:
			city_name = spot_data['place']['cityName']
			city_name = city_name.replace("'",'`')

		except Exception as e:
			city_name = None

		# Check if the spots has stateName value
		try:
			state_name = spot_data['place']['stateName']
			state_name = state_name.replace("'",'`')
		except Exception as e:
			state_name = None

		query = "INSERT INTO spots (users_id,name,review,remarks,place_name,country_name,city_name,state_name, status_id,is_privated,lat,long,created_at,updated_at) VALUES ("+str(user_id)+",'"+str(spot_name)+"','"+str(review)+"','"+str(remarks)+"','"+str(place_name)+"','"+str(spot_data['place']['countryName'])+"','"+str(city_name)+"','"+str(state_name)+"',"+str(status_id)+","+str(is_privated)+","+str(spot_data['place']['point']['coordinates'][0])+","+str(spot_data['place']['point']['coordinates'][1])+",'"+spot_data['createdAt'].isoformat()+"',now()) RETURNING id"

		print (bcolors.OKBLUE + "Executing Spots data migration. Row: "+ str(i) + bcolors.ENDC)

		# PoSTGis geolocalization translate code from lat and long to geom and position fields
		pgcur.execute("UPDATE spots SET geom = ST_SetSRID(ST_MakePoint(long,lat),4326) and position ST_SetSRID(ST_MakePoint(long,lat),4326);")

		# Insert the current spot
		postgres_query_load(pgcon,pgcur,i,query)

		spot_id = pgcur.fetchone()[0]

		#----------------------------------------------------
		# Here will be the tag and spot tags generation

		# 1. Do the user action validation and if not exists, generate the user action
		# 2. Generate the tags
		# 3. Generate 
		#----------------------------------------------------

		'''
		# Generate user actions with type user action = 5 (Spots)
		query = "INSERT INTO user_actions (entity_action_id,types_user_actions_id,created_at) VALUES ("+str(spot_id)+","+str(5)+",'"+spot_data['createdAt'].isoformat()+"')"

		print (bcolors.OKBLUE + "Executing User_actions data migration. Row: "+ str(i) + bcolors.ENDC)

		# Insert the user_actions
		postgres_query_load(pgcon,pgcur,i,query)
		'''

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

		# This section is to insert in user_actions related with tags
		pgcur.execute("SELECT st.id,t.name FROM tags t, spots_tags st WHERE st.tags_id = t.id")
		json_data_tags = pgcur.fetchall()

		# If there almost one tag
		if(len(spot_data['tags'])>0):

			# For each tags list, search for the tag_id and compare them by name
			for j in spot_data['tags']:

				# For each row in the tags table
				for k in json_data_tags:

					# If the tags names are equals, get the tag_id from the spots_tags table
					if j == k[1]:
						tag_id=k[0]

							# Check if exist a previously user_action with type_user_action = 2 (Spots tags) for the current Spot
							pgcur.execute("SELECT id FROM user_actions WHERE spot_id="+str(spot_id)+" AND type_user_actions_id="+str(1));
							spots_data = pgcur.fetchone()

							# If not found a previously user_action with type_user_action = 2 (Spots tags) for the current Spot, insert it
							if not(spots_data):

								# Generate user actions with type user action = 2 (Spots tags)
								query = "INSERT INTO user_actions (type_user_actions_id,spot_id,created_at) VALUES ("+str(1)+","+str(spot_id)+",'"+spot_data['createdAt'].isoformat()+"')"

								print (bcolors.OKBLUE + "Executing User_action data migration. Row: "+ str(i) + bcolors.ENDC)

								# Insert the user_actions
								postgres_query_load(pgcon,pgcur,i,query)

	print (bcolors.OKBLUE + "Generating user_actions, spots, site_images and spot_categories seeders"+ bcolors.ENDC)

	# Generate all the seeders needed
	query = "SELECT json_agg(a.*) FROM (SELECT * FROM users) a"
	filename = "user"

	# Generate json user data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	query = "SELECT json_agg(a.*) FROM (SELECT * FROM user_actions) a"
	filename = "user_actions"

	# Generate json user_actions data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	# Generate all the seeders needed
	query = "SELECT json_agg(a.*) FROM (SELECT * FROM spots) a"
	filename = "spots"

	# Generate json spots data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	query = "SELECT json_agg(a.*) FROM (SELECT * FROM site_images) a"
	filename =  "site_images"

	# Generate json site_images data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	query = "SELECT json_agg(a.*) FROM (SELECT * FROM spot_categories) a"
	filename =  "spot_categories"

	# Generate json spot_categories data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

def mongo_tags_extraction(monCli,monDB,pgcon,pgcur):
	query = ""
	tag_name = ""
	user_id = None
	tag_id = None
	pgcur.execute("SELECT id,email FROM users")
	json_data_users = pgcur.fetchall()

	# Get all the tags data
	for i,tags_data in enumerate(monDB.tags.find()):
		# Search for the user_id of the user by email comparison
		for j in json_data_users:
			if tags_data['author'] == j[1]:
				user_id=j[0]
				tag_name=tags_data['_id']

		query = "INSERT INTO tags (name,created_at,updated_at) VALUES ('"+tag_name+"',now(),now()) RETURNING id"

		# For each mongo tags document, insert in postgres tags table
		postgres_query_load(pgcon,pgcur,i,query)

		tag_id = pgcur.fetchone()[0]

		query = "INSERT INTO spot_tags (users_id,tags_id,created_at,updated_at) VALUES ("+str(user_id)+","+str(tag_id)+",now(),now())"

		# Generate the relationship spot_tags data
		postgres_query_load(pgcon,pgcur,i,query)

		print (bcolors.OKBLUE + "Executing Tags data migration. Row: "+ str(i) + bcolors.ENDC)

	print (bcolors.OKBLUE + "Generating tags and spots_tags seeders"+ bcolors.ENDC)

	# Generate all the seeders needed
	query = "SELECT json_agg(a.*) FROM (SELECT id,name,created_at,updated_at,is_active,is_deleted FROM tags) a"
	filename = "tags"

	# Generate json tags data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	query = "SELECT json_agg(a.*) FROM (SELECT id,user_id,tags_id,created_at,updated_at,is_active,is_deleted FROM spots_tags) a"
	filename = "spots_tags"

	# Generate json spots_tags data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

def mongo_reports_extraction(monCli,monDB,pgcon,pgcur):
	
	spot_id = None
	reports_type_data_id = None
	pgcur.execute("SELECT id,users_id,name FROM spots")
	json_data_spots = pgcur.fetchall()

	pgcur.execute("SELECT id,name FROM reports_type")
	json_reports_type = pgcur.fetchall()

	# For reports, iterates over all the reports
	for i,reports_data in enumerate(monDB.reports.find()):
		for j,spots_data in enumerate(json_data_spots):
			# Searching the spot_id of the report by spot name comparison
			if str(reports_data['spot']['title']) == spots_data[2]:
				spot_id=spots_data[0]
				user_id=spots_data[1]

				# Searching the reports_type_data of the report by name comparison
				for k,reports_type_data in enumerate(json_reports_type):
					if str(reports_data['type']) == reports_type_data[1]:
						reports_type_data_id=reports_type_data[0]

				# Reports part
				query = "INSERT INTO reports_actions (users_id,entity_reported_id,report_types_id,type_user_reports_id,created_at,updated_at) VALUES ("+str(user_id)+","+str(spot_id)+","+str(reports_type_data_id)+","+str(2)+",'"+reports_data['date'].isoformat()+"',now())"

				spot_id = None

				print (bcolors.OKBLUE + "Executing reports data migration. Row: "+ str(i) + bcolors.ENDC)

				# Insert the reports
				postgres_query_load(pgcon,pgcur,i,query)
				break

	print (bcolors.OKBLUE + "Generating reports_actions seeder"+ bcolors.ENDC)

	# Generate all the seeders needed
	query = "SELECT json_agg(a.*) FROM (SELECT * FROM reports_actions) a"
	filename = "reports_actions"

	# Generate json user data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

def mongo_collections_extraction(monCli,monDB,pgcon,pgcur):
	
	spot_id = None
	collection_id = None
	state_name = None
	city_name = None
	collections_query = ""
	pgcur.execute("SELECT id,country_name,state_name,city_name FROM spots")
	json_data_spots = pgcur.fetchall()

	pgcur.execute("SELECT id,name FROM category")
	json_categories_type = pgcur.fetchall()

	# For all the place_summaries (collections), iterates over all the reports
	for i,collections_data in enumerate(monDB.place_summaries.find()):
		for j,spots_data in enumerate(json_data_spots):

			# Check if the spots has cityName value
			try:
				city_name = collections_data['lastLocation']['cityName']
				city_name = city_name.replace("'",'`')
			except Exception as e:
				city_name = None

			# Check if the spots has stateName value
			try:
				state_name = collections_data['lastLocation']['stateName']
				state_name = state_name.replace("'",'`')
			except Exception as e:
				state_name = None

			# If the spots has city name and state name
			if(city_name and state_name):

				# Search the spots for every collection and compare it with the spots
				if (str(collections_data['lastLocation']['countryName']) == spots_data[1] and
					state_name == spots_data[2] and city_name == spots_data[3]):

					# Get the spot_id
					spot_id=spots_data[0]

					# Check if the current collection name already exists
					pgcur.execute("SELECT id,name FROM collections WHERE name ='"+collections_data['name']+"'")
					collections_query = pgcur.fetchall()

					# If found the collection, get the id
					if collections_query:

						collection_id = collections_query[0][0]

					# If not found the collection, insert it
					else:

						# Collections part
						query = "INSERT INTO collections (name,created_at,updated_at) VALUES ('"+str(collections_data['name'])+"','"+collections_data['createdAt'].isoformat()+"',now()) RETURNING id"

						print (bcolors.OKBLUE + "Executing collection data migration. Row: "+ str(i) + bcolors.ENDC)

						# Insert the collection
						postgres_query_load(pgcon,pgcur,i,query)

						collection_id = pgcur.fetchone()[0]

					# spots_collections part
					query = "INSERT INTO spots_collections (spot_id,collection_id,created_at,updated_at) VALUES ("+str(spot_id)+",'"+str(collection_id)+"','"+collections_data['createdAt'].isoformat()+"',now())"

					print (bcolors.OKBLUE + "Executing spots_collections data migration. Row: "+ str(i) + bcolors.ENDC)

					# Insert the spots_collections
					postgres_query_load(pgcon,pgcur,i,query)

			# If the spots hasn't city name but has state name
			elif(city_name != None and state_name == None):

				# Search the spots for every collection and compare it with the spots
				if (str(collections_data['lastLocation']['countryName']) == spots_data[1] and
					str(collections_data['lastLocation']['cityName']) == spots_data[3]):

					# Get the spot_id
					spot_id=spots_data[0]

					# Check if the current collection name already exists
					pgcur.execute("SELECT id,name FROM collections WHERE name ='"+collections_data['name']+"'")
					collections_query = pgcur.fetchall()

					# If found the collection, get the id
					if collections_query:

						collection_id = collections_query[0][0]

					# If not found the collection, insert it
					else:

						# Collections part
						query = "INSERT INTO collections (name,created_at,updated_at) VALUES ('"+str(collections_data['name'])+"','"+collections_data['createdAt'].isoformat()+"',now()) RETURNING id"

						print (bcolors.OKBLUE + "Executing collection data migration. Row: "+ str(i) + bcolors.ENDC)

						# Insert the collection
						postgres_query_load(pgcon,pgcur,i,query)

						collection_id = pgcur.fetchone()[0]

					# spots_collections part
					query = "INSERT INTO spots_collections (spot_id,collection_id,created_at,updated_at) VALUES ("+str(spot_id)+",'"+str(collection_id)+"','"+collections_data['createdAt'].isoformat()+"',now())"

					print (bcolors.OKBLUE + "Executing spots_collections data migration. Row: "+ str(i) + bcolors.ENDC)

					# Insert the spots_collections
					postgres_query_load(pgcon,pgcur,i,query)

			# If the spots has city name but hasn't state name
			elif(city_name == None and state_name != None):				

				# Search the spots for every collection and compare it with the spots
				if (str(collections_data['lastLocation']['countryName']) == spots_data[1] and
					str(collections_data['lastLocation']['stateName']) == spots_data[2]):

					# Get the spot_id
					spot_id=spots_data[0]

					# Check if the current collection name already exists
					pgcur.execute("SELECT id,name FROM collections WHERE name ='"+collections_data['name']+"'")
					collections_query = pgcur.fetchall()

					# If found the collection, get the id
					if collections_query:

						collection_id = collections_query[0][0]

					# If not found the collection, insert it
					else:

						# Collections part
						query = "INSERT INTO collections (name,created_at,updated_at) VALUES ('"+str(collections_data['name'])+"','"+collections_data['createdAt'].isoformat()+"',now()) RETURNING id"

						print (bcolors.OKBLUE + "Executing collection data migration. Row: "+ str(i) + bcolors.ENDC)

						# Insert the collection
						postgres_query_load(pgcon,pgcur,i,query)

						collection_id = pgcur.fetchone()[0]

					# spots_collections part
					query = "INSERT INTO spots_collections (spot_id,collection_id,created_at,updated_at) VALUES ("+str(spot_id)+",'"+str(collection_id)+"','"+collections_data['createdAt'].isoformat()+"',now())"

					print (bcolors.OKBLUE + "Executing spots_collections data migration. Row: "+ str(i) + bcolors.ENDC)

					# Insert the spots_collections
					postgres_query_load(pgcon,pgcur,i,query)

	print (bcolors.OKBLUE + "Generating collections and spots_collections seeders"+ bcolors.ENDC)

	# Generate all the seeders needed
	query = "SELECT json_agg(a.*) FROM (SELECT * FROM collections) a"
	filename = "collections"

	# Generate json collections data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

	# Generate all the seeders needed
	query = "SELECT json_agg(a.*) FROM (SELECT * FROM spots_collections) a"
	filename = "spots_collections"

	# Generate json spots_collections data
	postgres_json_export_to_file(pgcon,pgcur,query,filename)

def main():
	monCli, monDB = mongoConnection()
	pgcon, pgcur = postgresConnection()	

	mongo_user_extraction(monCli,monDB,pgcon,pgcur)
	mongo_friends_extraction(monCli,monDB,pgcon,pgcur)
	mongo_spots_extraction(monCli,monDB,pgcon,pgcur)
	mongo_tags_extraction(monCli,monDB,pgcon,pgcur)
	mongo_reports_extraction(monCli,monDB,pgcon,pgcur)
	mongo_collections_extraction(monCli,monDB,pgcon,pgcur)

	pgcon.close()
	pgcur.close()	

if __name__ == '__main__':
    main()

#!/usr/bin/python3
from databases_connection import *
import psycopg2, psycopg2.extras
import json
import datetime
import time
import re
import os
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

def postgres_delete_all(pgcur):
	pgcur.execute("DELETE FROM collections")
	pgcur.execute("DELETE FROM spot_collections")
	pgcur.execute("DELETE FROM users")
	pgcur.execute("DELETE FROM friendships")
	pgcur.execute("DELETE FROM spots")
	pgcur.execute("DELETE FROM tags")
	pgcur.execute("DELETE FROM site_images")
	pgcur.execute("DELETE FROM spot_categories")
	pgcur.execute("DELETE FROM categories")
	pgcur.execute("DELETE FROM user_actions")
	pgcur.execute("DELETE FROM spot_tags")
	pgcur.execute("DELETE FROM reports_types")
	pgcur.execute("DELETE FROM reports_actions")

def postgres_restart_sequences(pgcur):
	pgcur.execute("ALTER SEQUENCE collections_id_seq RESTART WITH 1")
	pgcur.execute("ALTER SEQUENCE spot_collections_id_seq RESTART WITH 1")
	pgcur.execute("ALTER SEQUENCE users_id_seq RESTART WITH 1")
	pgcur.execute("ALTER SEQUENCE friendships_id_seq RESTART WITH 1")
	pgcur.execute("ALTER SEQUENCE spots_id_seq RESTART WITH 1")
	pgcur.execute("ALTER SEQUENCE tags_id_seq RESTART WITH 1")
	pgcur.execute("ALTER SEQUENCE site_images_id_seq RESTART WITH 1")
	pgcur.execute("ALTER SEQUENCE spot_categories_id_seq RESTART WITH 1")
	pgcur.execute("ALTER SEQUENCE categories_id_seq RESTART WITH 1")
	pgcur.execute("ALTER SEQUENCE user_actions_id_seq RESTART WITH 1")
	pgcur.execute("ALTER SEQUENCE spot_tags_id_seq RESTART WITH 1")
	pgcur.execute("ALTER SEQUENCE reports_types_id_seq RESTART WITH 1")
	pgcur.execute("ALTER SEQUENCE reports_actions_id_seq RESTART WITH 1")

def mongo_collections_list(monCli,monDB):
	# get and list all the mongodb collections
	collections = dict((monDB, [collection for collection in monCli[monDB].list_collection_names(include_system_collections=False)])
		for monDB in monCli.list_database_names())
	return collections

def postgres_query_load(pgcon,pgcur,query):
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
	user_collection_name = collections['ibeen'][2]
	user_collection_data = monDB[user_collection_name]
	query = ""
	first_name = ""
	last_name = ""
	full_name = ""
	#x = user_collection_data.find_one()
	# Get all the user data
	for i,user_data in enumerate(user_collection_data.find()):
		if(i >1):
			query = "INSERT INTO users (first_name,last_name,full_name,email,status_account,created_at,updated_at) VALUES ('"+first_name+"','"+last_name+"','"+full_name+"','"+user_data['email']['value']+"',1,'"+user_data['createdOn']['instant'].isoformat()+"',now())"
			# for each mongo user document, insert in postgres user table
			postgres_query_load(pgcon,pgcur,query)
			#time.sleep(5)
			# pprint(data)
			print (bcolors.OKBLUE + "Executing User data migration. Row: "+ str(i) + bcolors.ENDC)

	# This part will be overwritten in spot migration
	# Generate all the seeders needed
	'''
	query = "SELECT json_agg(a.*) FROM (SELECT id, email, status_account, created_at, updated_at, is_active, is_deleted FROM users) a"
	filename = "user"
''
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

		if (user_id != friend_id):

			pgcur.execute("select friendable_id,friend_id from friendships where (friendable_id ="+str(friend_id)+" and friend_id="+str(user_id)+")")

			# Only insert this friendship it not exists
			if not pgcur.fetchone():

				print (bcolors.OKBLUE + "Executing Friendships data migration. Row: "+ str(i) + bcolors.ENDC)

				query = "INSERT INTO friendships (friend_id,friendable_type,friendable_id,status,created_at,updated_at) VALUES ("+str(user_id)+",'User',"+str(friend_id)+",2,'"+friends_data['createdAt'].isoformat()+"',now())"

				# For each mongo friendships document, insert in postgres friendships table the first relationship: A is friend of B
				postgres_query_load(pgcon,pgcur,query)

				query = "INSERT INTO friendships (friend_id,friendable_type,friendable_id,status,created_at,updated_at) VALUES ("+str(friend_id)+",'User',"+str(user_id)+",2,'"+friends_data['createdAt'].isoformat()+"',now())"

				# For each mongo friendships document, insert in postgres friendships table the second relationship: B is friend of A
				postgres_query_load(pgcon,pgcur,query)

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
				pgcur.execute("UPDATE users SET first_name = '"+first_name+"', last_name = '"+last_name+"', full_name='"+friends_data['user']['fullname']+"' WHERE id="+str(user_id))

	#print (bcolors.OKBLUE + "Generating friendships seeder"+ bcolors.ENDC)

	# Generate all the seeders needed
	#query = "SELECT json_agg(a.*) FROM (SELECT id,friendable_type,friendable_id,friend_id,created_at,updated_at,blocker_id,status FROM friendships) a"
	#filename = "friendships"

	# Generate json friendships data
	#postgres_json_export_to_file(pgcon,pgcur,query,filename)

def mongo_spots_extraction(monCli,monDB,pgcon,pgcur):
	query = ""
	user_id = None
	first_name = ""
	last_name = ""	
	full_user_name = ""
	category_id = None
	tag_name = None
	tag_id = None
	spot_id = None
	spots_tags_id = None
	status_id = None
	review = ""
	remarks = ""
	place_name = ""
	spot_name = None
	is_privated = False
	city_name = ""
	state_name = ""
	full_address = None
	user_validator = False
	category_validator = False
	pgcur.execute("SELECT id,email FROM users")
	json_data_users = pgcur.fetchall()

	pgcur.execute("SELECT id,name FROM categories")
	json_data_category = pgcur.fetchall()

	# Get tags id and names
	pgcur.execute("SELECT id,name FROM tags")
	json_data_tags = pgcur.fetchall()

	# Get all the spots data
	for i,spot_data in enumerate(monDB.spots.find()):
		# Searching the user_id of the user by email comparison
		for j in json_data_users:
			user_validator = False
			if spot_data['user']['_id'] == j[1]:
				user_id=j[0]
				user_validator = True
				break

		if not(user_validator):
			query = "INSERT INTO users (email,status_account,created_at,updated_at) VALUES ('"+spot_data['user']['email']+"',1,'"+spot_data['createdAt'].isoformat()+"',now()) RETURNING id"

			# for each mongo new user document, insert in postgres user table
			postgres_query_load(pgcon,pgcur,query)
			user_id = pgcur.fetchone()[0]

			# Reload the users query
			pgcur.execute("SELECT id,email FROM users")
			json_data_users = pgcur.fetchall()

			print (bcolors.OKBLUE + "New user found. Row: "+ spot_data['user']['_id'] + bcolors.ENDC)

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
		pgcur.execute("UPDATE users SET first_name = '"+first_name+"', last_name = '"+last_name+"', full_name = '"+spot_data['user']['fullname']+"' WHERE id="+str(user_id))

		# Check if the spots has review value
		try:
			# Remove emoticons
			review = re.sub(r'[^\w]', ' ', spot_data['review'])
		except Exception as e:
			pass

		# Check if the spots has remarks value
		try:
			# Remove emoticons
			remarks = re.sub(r'[^\w]', ' ', spot_data['remarks'])
		except Exception as e:
			pass

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
		# Remove emoticons
		spot_name = re.sub(r'[^\w]', ' ', spot_name)

		# Check if the spots has name value
		try:
			place_name = spot_data['place']['name'].replace("'",'`')
		except Exception as e:
			pass

		# Check if the spots has cityName value
		try:
			city_name = spot_data['place']['cityName']
			city_name = city_name.replace("'",'`')
		except Exception as e:
			pass

		# Check if the spots has stateName value
		try:
			state_name = spot_data['place']['stateName']
			state_name = state_name.replace("'",'`')
		except Exception as e:
			pass

		full_address = str(spot_data['place']['countryName']) + ', ' + city_name

		query = "INSERT INTO spots (users_id,name,review,remarks,place_name,country_name,city_name,state_name, status_id,is_privated,lat,long,created_at,updated_at,full_address) VALUES ("+str(user_id)+",'"+str(spot_name)+"','"+str(review)+"','"+str(remarks)+"','"+str(place_name)+"','"+str(spot_data['place']['countryName'])+"','"+str(city_name)+"','"+str(state_name)+"',"+str(status_id)+","+str(is_privated)+","+str(spot_data['place']['point']['coordinates'][0])+","+str(spot_data['place']['point']['coordinates'][1])+",'"+spot_data['createdAt'].isoformat()+"',now(),'"+full_address+"') RETURNING id"

		print (bcolors.OKBLUE + "Executing Spots data migration. Row: "+ str(i) + bcolors.ENDC)

		# PoSTGis geolocalization translate code from lat and long to geom and position fields
		#pgcur.execute("UPDATE spots SET geom = ST_SetSRID(ST_MakePoint(long,lat),4326) and position ST_SetSRID(ST_MakePoint(long,lat),4326);")

		# Insert the current spot

		postgres_query_load(pgcon,pgcur,query)

		spot_id = pgcur.fetchone()[0]

		'''
		# Generate user actions with type user action = 5 (Spots)
		query = "INSERT INTO user_actions (entity_action_id,types_user_actions_id,created_at) VALUES ("+str(spot_id)+","+str(5)+",'"+spot_data['createdAt'].isoformat()+"')"

		print (bcolors.OKBLUE + "Executing User_actions data migration. Row: "+ str(i) + bcolors.ENDC)

		# Insert the user_actions
		postgres_query_load(pgcon,pgcur,query)
		'''

		# Searching the category_id of the spot category name comparison
		for j in json_data_category:
			category_validator = False			
			if spot_data['categoryId'] == j[1]:
				category_id=j[0]
				category_validator = True
				break
		if not category_validator:
			query = "INSERT INTO categories (name,created_at,updated_at) VALUES ('"+spot_data['categoryId']+"','"+spot_data['createdAt'].isoformat()+"',now()) RETURNING id"

			# Insert the categories data
			postgres_query_load(pgcon,pgcur,query)

			category_id = pgcur.fetchone()[0]

			print (bcolors.OKBLUE + "Executing Categories data migration. Category Id: "+ str(category_id) + bcolors.ENDC)

			# Reload categories query
			pgcur.execute("SELECT id,name FROM categories")
			json_data_category = pgcur.fetchall()

		query = "INSERT INTO spot_categories (spots_id,category_id,created_at,updated_at) VALUES ("+str(spot_id)+","+str(category_id)+",'"+spot_data['createdAt'].isoformat()+"',now())"

		print (bcolors.OKBLUE + "Executing Spots_categories data migration. Row: "+ str(i) + bcolors.ENDC)

		# Insert the spot_categories data
		postgres_query_load(pgcon,pgcur,query)				

		# For each gallery, iterates over all images
		for j,gallery_data in enumerate(spot_data['gallery']):

			query = "INSERT INTO site_images (spots_id,uri,extension,principalimage,original,created_at,updated_at) VALUES ("+str(spot_id)+",'"+gallery_data['images']['uri']+"','"+gallery_data['extension']+"','"+str(gallery_data['principalImage'])+"','"+gallery_data['images']['type']+"','"+gallery_data['created'].isoformat()+"',now())"

			print (bcolors.OKBLUE + "Executing Site_Images data migration. Row: "+ str(j) + " of the Spot row: " + str(i) + " iteration" + bcolors.ENDC)

			# Insert the data image
			postgres_query_load(pgcon,pgcur,query)

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

					query = "INSERT INTO tags (name,created_at,updated_at) VALUES ('"+j+"','"+spot_data['createdAt'].isoformat()+"',now()) RETURNING id"

					# Insert the new tag
					postgres_query_load(pgcon,pgcur,query)

					tag_id = pgcur.fetchone()[0]

					# Reload the tags query
					pgcur.execute("SELECT id,name FROM tags")
					json_data_tags = pgcur.fetchall()

				# Then generate the user_action related with the tag
				# So, first, check if exists a previously user_action with 
				# type_user_action = 1 (Spots tags) for the current Spot
				pgcur.execute("SELECT id FROM user_actions WHERE spots_id="+str(spot_id)+" AND type_user_actions_id="+str(1));
				try:
					user_actions = pgcur.fetchone()[0]
				except Exception as e:
					user_actions = False

				# If not found a previously user_action with type_user_action = 1 (Spots tags) for the current Spot, insert it
				if not user_actions:

					# Generate user actions with type user action = 1 (Spots tags)
					query = "INSERT INTO user_actions (type_user_actions_id,spots_id,created_at,updated_at) VALUES ("+str(1)+","+str(spot_id)+",'"+spot_data['createdAt'].isoformat()+"',now()) RETURNING id"

					print (bcolors.OKBLUE + "Executing User_action data migration. Row: "+ str(i) + bcolors.ENDC)

					# Insert the user_actions
					postgres_query_load(pgcon,pgcur,query)
				
					user_actions = pgcur.fetchone()[0]

				# If found a previously user_action with type_user_action = 1 (Spots tags) for the current Spot, do not do nothing
				else:
					pass

				# Finally, in any case (tag already exist or new tag) insert a new spot_tag with the current tag_id
				query = "INSERT INTO spot_tags (users_id,user_actions_id,tags_id,created_at,updated_at) VALUES ("+str(user_id)+","+str(user_actions)+","+str(tag_id)+",'"+spot_data['createdAt'].isoformat()+"',now())"

				# Insert the current spots_tags
				postgres_query_load(pgcon,pgcur,query)

	#print (bcolors.OKBLUE + "Generating user_actions, spots, site_images and spot_categories seeders"+ bcolors.ENDC)

	# # Generate all the seeders needed
	# query = "SELECT json_agg(a.*) FROM (SELECT * FROM users) a"
	# filename = "user"

	# # Generate json user data
	# postgres_json_export_to_file(pgcon,pgcur,query,filename)

	# query = "SELECT json_agg(a.*) FROM (SELECT * FROM user_actions) a"
	# filename = "user_actions"

	# # Generate json user_actions data
	# postgres_json_export_to_file(pgcon,pgcur,query,filename)

	# # Generate all the seeders needed
	# query = "SELECT json_agg(a.*) FROM (SELECT * FROM spots) a"
	# filename = "spots"

	# #query = "select json_agg(a.*) from (select * from spots where id = 803) a"

	# # Generate json spots data
	# postgres_json_export_to_file(pgcon,pgcur,query,filename)

	# query = "SELECT json_agg(a.*) FROM (SELECT * FROM site_images) a"
	# filename =  "site_images"

	# # Generate json site_images data
	# postgres_json_export_to_file(pgcon,pgcur,query,filename)

	# query = "SELECT json_agg(a.*) FROM (SELECT * FROM spot_categories) a"
	# filename =  "spot_categories"

	# # Generate json spot_categories data
	# postgres_json_export_to_file(pgcon,pgcur,query,filename)

def mongo_reports_extraction(monCli,monDB,pgcon,pgcur):
	
	spot_id = None
	reports_type_id = None
	json_reports_type = None
	json_reports_type_validator = False

	# Query to spots table
	pgcur.execute("SELECT id,users_id,name FROM spots")
	json_data_spots = pgcur.fetchall()

	# Query to reports type table
	pgcur.execute("SELECT id,name FROM reports_types")
	json_reports_type = pgcur.fetchall()

	# For reports, iterates over all the reports
	for i,reports_data in enumerate(monDB.reports.find()):
		for j,spots_data in enumerate(json_data_spots):
			# Searching the spot_id of the report by spot name comparison
			if str(reports_data['spot']['title']) == spots_data[2]:
				spot_id=spots_data[0]
				user_id=spots_data[1]

				# Searching the reports_type_id of reports action by type comparison
				for j in json_reports_type:
					json_reports_type_validator = False
					if reports_data['type'] == j[1]:
						reports_type_id=j[0]
						json_reports_type_validator = True
						break

				if not json_reports_type_validator:
					query = "INSERT INTO reports_types (name,created_at,updated_at) VALUES ('"+reports_data['type']+"',now(), now()) RETURNING id"

					# Insert the reports type data
					postgres_query_load(pgcon,pgcur,query)

					reports_type_id = pgcur.fetchone()[0]

					print (bcolors.OKBLUE + "Executing Reports Type data migration. Reports Types Id: "+ str(reports_type_id) + bcolors.ENDC)

					# Reload reports type query
					pgcur.execute("SELECT id,name FROM reports_types")
					json_reports_type = pgcur.fetchall()

				# Reports part
				query = "INSERT INTO reports_actions (users_id,entity_reported_id,report_types_id,type_user_reports_id,created_at,updated_at) VALUES ("+str(user_id)+","+str(spot_id)+","+str(reports_type_id)+","+str(2)+",'"+reports_data['date'].isoformat()+"',now())"

				spot_id = None

				print (bcolors.OKBLUE + "Executing reports data migration. Row: "+ str(i) + bcolors.ENDC)

				# Insert the reports
				postgres_query_load(pgcon,pgcur,query)
				break

	#print (bcolors.OKBLUE + "Generating reports_actions seeder"+ bcolors.ENDC)

	# Generate all the seeders needed
	#query = "SELECT json_agg(a.*) FROM (SELECT * FROM reports_actions) a"
	#filename = "reports_actions"

	# Generate json user data
	#postgres_json_export_to_file(pgcon,pgcur,query,filename)

def mongo_collections_extraction(monCli,monDB,pgcon,pgcur):
	
	spot_id = None
	collection_id = None
	state_name = None
	city_name = None
	collections_query = ""
	pgcur.execute("SELECT id,country_name,state_name,city_name FROM spots")
	json_data_spots = pgcur.fetchall()

	pgcur.execute("SELECT id,name FROM categories")
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
						postgres_query_load(pgcon,pgcur,query)

						collection_id = pgcur.fetchone()[0]

					# spot_collections part
					query = "INSERT INTO spot_collections (spots_id,collections_id,created_at,updated_at) VALUES ("+str(spot_id)+",'"+str(collection_id)+"','"+collections_data['createdAt'].isoformat()+"',now())"

					print (bcolors.OKBLUE + "Executing spot_collections data migration. Row: "+ str(i) + bcolors.ENDC)

					# Insert the spot_collections
					postgres_query_load(pgcon,pgcur,query)

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
						postgres_query_load(pgcon,pgcur,query)

						collection_id = pgcur.fetchone()[0]

					# spot_collections part
					query = "INSERT INTO spot_collections (spots_id,collections_id,created_at,updated_at) VALUES ("+str(spot_id)+",'"+str(collection_id)+"','"+collections_data['createdAt'].isoformat()+"',now())"

					print (bcolors.OKBLUE + "Executing spot_collections data migration. Row: "+ str(i) + bcolors.ENDC)

					# Insert the spot_collections
					postgres_query_load(pgcon,pgcur,query)

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
						postgres_query_load(pgcon,pgcur,query)

						collection_id = pgcur.fetchone()[0]

					# spot_collections part
					query = "INSERT INTO spot_collections (spots_id,collections_id,created_at,updated_at) VALUES ("+str(spot_id)+",'"+str(collection_id)+"','"+collections_data['createdAt'].isoformat()+"',now())"

					print (bcolors.OKBLUE + "Executing spot_collections data migration. Row: "+ str(i) + bcolors.ENDC)

					# Insert the spot_collections
					postgres_query_load(pgcon,pgcur,query)

	#print (bcolors.OKBLUE + "Generating collections and spot_collections seeders"+ bcolors.ENDC)

	# Generate all the seeders needed
	#query = "SELECT json_agg(a.*) FROM (SELECT * FROM collections) a"
	#filename = "collections"

	# Generate json collections data
	#postgres_json_export_to_file(pgcon,pgcur,query,filename)

	# Generate all the seeders needed
	#query = "SELECT json_agg(a.*) FROM (SELECT * FROM spot_collections) a"
	#filename = "spot_collections"

	# Generate json spot_collections data
	#postgres_json_export_to_file(pgcon,pgcur,query,filename)

def main():
	try:
		monCli, monDB = mongoConnection()
		pgcon, pgcur = postgresConnection()
	except Exception as e:
		print (bcolors.OKGREEN + "Connection with mongo or postgres database failed: " + str(e) + bcolors.ENDC)
		os._exit(0)

	postgres_delete_all(pgcur)
	postgres_restart_sequences(pgcur)
	mongo_user_extraction(monCli,monDB,pgcon,pgcur)
	mongo_friends_extraction(monCli,monDB,pgcon,pgcur)
	mongo_spots_extraction(monCli,monDB,pgcon,pgcur)
	mongo_reports_extraction(monCli,monDB,pgcon,pgcur)
	mongo_collections_extraction(monCli,monDB,pgcon,pgcur)
	print (bcolors.OKGREEN + "Data migration process finished successfully " + bcolors.ENDC)

	pgcon.close()
	pgcur.close()	

if __name__ == '__main__':
    main()

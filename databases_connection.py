#!/usr/bin/python3
import os
from configparser import RawConfigParser
import psycopg2, psycopg2.extras
from pymongo import MongoClient
import pymongo

BASE_DIR = os.getcwd()
config = RawConfigParser()
config.read(BASE_DIR + '/settings.ini')

DATABASES = {
    'postgresql': {
        'NAME': config.get('pgConf', 'DB_NAME'),
        'USER': config.get('pgConf', 'DB_USER'),
        'PASSWORD': config.get('pgConf', 'DB_PASS'),
        'HOST': config.get('pgConf', 'DB_HOST'),
        'PORT': config.get('pgConf', 'DB_PORT'),
    },
    'mongodb': {
        'NAME': config.get('mongoConf', 'DB_NAME'),
        'USER': config.get('mongoConf', 'DB_USER'),
        'PASSWORD': config.get('mongoConf', 'DB_PASS'),
        'HOST': config.get('mongoConf', 'DB_HOST'),
        'PORT': config.get('mongoConf', 'DB_PORT'),
    }
}

def postgresConnection():
	try:
		conn = psycopg2.connect(
			database=DATABASES['postgresql']['NAME'],
			user=DATABASES['postgresql']['USER'],
			password=DATABASES['postgresql']['PASSWORD'],
			host=DATABASES['postgresql']['HOST'],
			port=DATABASES['postgresql']['PORT']
			)
		curs = conn.cursor()
	except (Exception,psycopg2.DatabaseError) as e:
		print ("Postgres connection is not ready yet. Error: " + str(e))
	return [conn, curs]

def mongoConnection():
	try:
		mongoClient = pymongo.MongoClient(
				DATABASES['mongodb']['HOST'], 
				int(DATABASES['mongodb']['PORT'])
				)
		mongodbName = mongoClient[DATABASES['mongodb']['NAME']]
	except Exception as e:
		print ("Mongodb connection is not ready yet. Error: " + str(e))
	return [mongoClient, mongodbName]

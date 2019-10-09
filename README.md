# python-pymongo-tests

Summary
---------------
This is a repository used to migrate data from a MongoDB old system to a new PostgreSQL system, using pymongo and psycopg2 to generate ETL process scripts 

## Installation

The following steps were applied to install this project. Create virtualenv and install the requirements:

	virtualenv env --python=python3
	source env/bin/activate

	pip install -r requirements.txt

Create a **settings.ini** file, with the structure as below:

    [pgConf]
    DB_NAME=dbname
    DB_USER=user
    DB_PASS=password
    DB_HOST=host
    DB_PORT=port

    [mongoConf]
    DB_NAME=dbname
    DB_USER=user
    DB_PASS=password
    DB_HOST=port
    DB_PORT=port

## Collections and Tables Equivalences

MongoDB | PostgreSQL
-- | -- |
users | users
friends | friendships
categories | categories
tags | spot_tags, tags
reports | reports_actions
place_summaries | collections, spots_collections
spots | spots, user_actions, site_images
reports | reports_actions

## Contributions
------------------------

All work to improve performance is good

Enjoy it!

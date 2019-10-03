psql -U postgres -a -f ./main_database.sql
psql -U postgres -d result_database -a -f ./public/tables/users.sql
psql -U postgres -d result_database -a -f ./public/tables/friendships.sql
psql -U postgres -d result_database -a -f ./public/tables/tags.sql
psql -U postgres -d result_database -a -f ./public/tables/spot_tags.sql
psql -U postgres -d result_database -a -f ./public/tables/spots.sql
psql -U postgres -d result_database -a -f ./public/tables/user_actions.sql
psql -U postgres -d result_database -a -f ./public/tables/spot_categories.sql
psql -U postgres -d result_database -a -f ./public/tables/site_images.sql
psql -U postgres -d result_database -a -f ./public/tables/tags.sql
psql -U postgres -d result_database -a -f ./public/tables/spot_tags.sql
psql -U postgres -d result_database -a -f ./public/tables/categories.sql
psql -U postgres -d result_database -a -f ./public/tables/spot_categories.sql
psql -U postgres -d result_database -a -f ./public/tables/friendships.sql
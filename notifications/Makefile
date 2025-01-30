up:
	docker-compose up -d --build

down:
	docker-compose down --remove-orphans

down-clear:
	docker-compose down -v --remove-orphans

remove_storage_from_etl:
	rm -rf postgres_to_es/storage.json || true

init: remove_storage_from_etl env_file_copy up create_schema_and_populate_from_sqlite django-migrate \
		django-create-superuser django-collectstatic es_create_schema flask-apply-initial-migrations \
		flask-test-apply-initial-migrations flask-test-create-privileged-user flask-test-create-admin

env_file_copy:
	cp .env.sample .env

create_schema_and_populate_from_sqlite:
	docker-compose run --rm etl-cli python es_pgsql_initial_population/move_from_sqlite/load_data.py

django-migrate:
	docker-compose exec django ./manage.py migrate --fake movies 0001
	docker-compose exec django ./manage.py migrate

django-create-superuser:
	docker-compose exec django ./manage.py createsuperuser

django-collectstatic:
	docker-compose exec django ./manage.py collectstatic --noinput


es_create_schema:
	 docker-compose run --rm etl-cli python es_pgsql_initial_population/create_schema.py

es_transfer_from_postgres_pipline_start:
	docker-compose run --rm etl-cli python main.py

runtests: test_notification_api
	docker-compose run --rm tests-cli pytest functional/src

populate_test_data:
	docker-compose run --rm tests-cli python initial_test_data_population.py


flask-init-db:
	docker-compose exec auth-flask flask db init

flask-create-initial-migrations:
	docker-compose exec auth-flask flask db migrate -m "Initial migration."

# миграции стартуем тут, не в Dockerfile - для контроля
flask-apply-initial-migrations:
	docker-compose exec auth-flask bash -c 'while !</dev/tcp/auth-db/5432; do sleep 1; done; flask db upgrade'

# миграции стартуем тут, не в Dockerfile - для контроля
flask-test-apply-initial-migrations:
	docker-compose exec auth-flask-test bash -c 'while !</dev/tcp/auth-db-test/5432; do sleep 1; done; flask db upgrade'

flask-test-create-privileged-user:
	docker-compose exec auth-flask-test flask command create-privileged-user priv@mail.ru

flask-test-create-admin:
	docker-compose exec auth-flask-test flask command create-admin admin@test.ru

ugc_generate_data:
	docker-compose exec ugc python -m commands.populate_db

ugc_test_speed:
	docker-compose exec ugc python -m commands.test_ugc_speed

ugc_lint:
	python -m pip install flake8 wemake-python-styleguide flake8-html mypy lxml --ignore-installed PyYAML
	flake8 ugc
	mypy --html-report ./mypy-report --install-types --non-interactive --disallow-untyped-calls ugc

test_notification_api:
	docker-compose up --build notification-api-test
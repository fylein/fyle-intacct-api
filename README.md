# Fyle Sage Intacct API
Django Rest Framework API for Fyle Sage Intacct Integration


### Setup

* ### Adding a New View, Function, or Trigger:
    Follow these steps to ensure your changes are applied correctly:

    1. **Make changes** in the [`fyle-integrations-db-migrations`](https://github.com/fylein/fyle-integrations-db-migrations) repository.
    2. **Update the submodule** in the Intacct API:
        ```bash
        git submodule init
        git submodule update
        ```
    3. **Enter the Intacct API container**:
        ```bash
        enter intacct-api
        ```
    4. **Generate a migration file** using the provided convenient command:
        ```bash
        python3 manage.py create_sql_migration <file-path1>
        ```
        - Replace `<file-path1>` with the relative path to your SQL file from the fyle-integrations-db-migrations folder.
        - The migration will always be created in the `internal` app.

        **Example:**
        ```bash
        python3 manage.py create_sql_migration fyle-integrations-db-migrations/Intacct/functions/re_export_expenses_Intacct.sql
        ```

    5. **Review the newly generated migration file**:
        Navigate to the `apps/internal/migrations/` directory and ensure the migration file content is as expected.

    6. **Restart the Intacct API service and apply the migration**:
        ```bash
        restart intacct-api
        logs intacct-api
        ```
        Confirm in the logs that the migration has been applied successfully.

* Download and install Docker desktop for Mac from [here.](https://www.docker.com/products/docker-desktop)

* If you're using a linux machine, please download docker according to the distrubution you're on.

* Rename docker-compose.yml.template to docker-compose.yml

    ```
    $ mv docker-compose.yml.template docker-compose.yml
    ```

* Setup environment variables in docker_compose.yml

    ```yaml
    environment:
      SECRET_KEY: thisisthedjangosecretkey
      ENCRYPTION_KEY:
      ALLOWED_HOSTS: "*"
      DEBUG: "False"
      API_URL: http://localhost:8000/api
      DATABASE_URL: postgres://postgres:postgres@db:5432/intacct_db
      FYLE_BASE_URL:
      FYLE_CLIENT_ID:
      FYLE_CLIENT_SECRET:
      FYLE_TOKEN_URI:
      FYLE_JOBS_URL:
      SI_SENDER_ID:
      SI_SENDER_PASSWORD:
   ```

* Build docker images

    ```
    docker-compose build api qcluster
    ```

* Run docker containers

    ```
    docker-compose up -d db api qcluster
    ```

* The database can be accessed by this command, on password prompt type `postgres`

    ```
    docker-compose run -e PGPASSWORD=postgres db psql -h db -U postgres intacct_db
    ```

* To tail the logs a service you can do

    ```
    docker-compose logs -f <api / qcluster>
    ```

* To stop the containers

    ```
    docker-compose stop api qcluster
    ```

* To restart any containers - `would usually be needed with qcluster after you make any code changes`

    ```
    docker-compose restart qcluster
    ```

* To run bash inside any container for purpose of debugging do

    ```
    docker-compose exec api /bin/bash
    ```

# Django 4.2.26 security update

# Demo deployment using Docker

## Requirements

* docker: https://docs.docker.com/install/

## Installation

1. Get the source code
    
    ```bash
    git clone git@github.com:elixir-luxembourg/daisy.git
    cd daisy
    ```
1. Create your settings file
    
	```bash
	cp elixir_daisy/settings_local.template.py elixir_daisy/settings_local.py
	```
    Optional: edit the file elixir_daisy/settings_local.py to adapt to your environment.

1. Build daisy docker image  
    ```bash
    docker-compose up --build
    ```
    Wait for the build to finish and keep the process running
1. Open a new shell and go to daisy folder

1. Build the database
    
    ```bash
    docker-compose exec web python manage.py migrate
    ```
1. Build the solr schema

    ```bash
    docker-compose exec web python manage.py build_solr_schema -c /solr/daisy/conf -r daisy -u default
    ```

1. Compile and deploy static files
    
    ```bash
    docker-compose exec web python manage.py collectstatic
    ```
1. Create initial data in the database
    
    ```bash
    docker-compose exec web bash -c "cd core/fixtures/ && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/edda.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hpo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hdo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hgnc.json"
    docker-compose exec web python manage.py load_initial_data
    ```
   Initial data includes, for instance, controlled vocabularies terms and initial list of institutions and cohorts.  
   **This step can take several minutes to complete**
    
1. Load demo data
    
    ```bash
    docker-compose exec web python manage.py load_demo_data
    ```
    This will create mock datasets, projects and create an demo admin account.

1. Optional - import users from an active directory instance

    ```bash
    docker-compose exec web python manage.py import_users
    ```
    
1.  Build the search index

    ```bash
    docker-compose exec web python manage.py rebuild_index -u default
    ```    

1. Browse to https://localhost  
    a demo admin account is available:
    
    ```
        username: admin
        password: demo
    ```

## Operation manual


### Importing 

In addition to loading of initial data, DAISY database can be populated by importing Project, Dataset and Partners records from JSON files using commands `import_projects`, `import_datasets` and `import_partners` respectively.
 The commands for import are accepting one JSON file (flag `-f`): </br>

```bash
docker-compose exec web python manage.py <COMMAND> -f ${PATH_TO_JSON_FILE}
```
where ${PATH_TO_JSON_FILE} is the path to a json file containing the records definitions.
See file daisy/data/demo/projects.json as an example.
 
Alternatively, you can specify directory containing multiple JSON files to be imported with `-d` flag:
```bash
docker-compose exec web python manage.py <COMMAND> -d ${PATH_TO_DIR}
```

### Exporting  

Information in the DAISY database can be exported to JSON files. The command for export are given below:</br>

```bash
docker-compose exec web python manage.py export_partners -f ${JSON_FILE}
```
where ${JSON_FILE} is the path to a json file that will be produced.  In addition to ````export_partners````, you can run ````export_projects```` and ````export_datasets```` in the same way.

### Upgrade to last Daisy version

1. Create a database backup.

	```bash
	docker-compose exec db pg_dump daisy --port=5432 --username=daisy --no-password --clean > backup_`date +%y-%m-%d`.sql
	```
	
1. Make sure docker containers are stopped.

	```bash
	docker-compose stop
	```

3. Get last Daisy release.

	```bash
	git checkout master
	git pull
	```

1. Rebuild and start the docker containers.

	```bash
	docker-compose up --build
	```
	Open a new terminal window to execute the following commands.

1. Update the database schema.

	```bash
	docker-compose exec web python manage.py migrate
	```

1. Update the solr schema.

	```bash
	docker-compose exec web python manage.py build_solr_schema -c /solr/daisy/conf -r daisy -u default
	```

1. Collect static files.
 
	```bash
	docker-compose exec web python manage.py collectstatic
	```

	
1. Rebuild the search index.
    
    ```bash
    docker-compose exec web python manage.py rebuild_index -u default
    ```	
1. Reimport the users (optional).
	    
    If LDAP was used during initial setup to import users, they have to be imported again:
    
    ```bash
    docker-compose exec web python manage.py import_users
    ```

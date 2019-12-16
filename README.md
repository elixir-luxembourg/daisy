# Elixir Daisy
[![Build Status](https://travis-ci.com/elixir-luxembourg/daisy.svg?branch=develop)](https://travis-ci.com/elixir-luxembourg/daisy)

Data Information System (DAISY) is a data bookkeeping application designed to help Biomedical Research  institutions with their GDPR compliance.

## Using Docker

### Requirements

* docker: https://docs.docker.com/install/

### Installation

1. Get the source code
    
    ```bash
    git clone git@github.com:elixir-luxembourg/daisy.git
    cd daisy
    ```
2. Create your settings file
    
	```bash
	cp elixir_daisy/settings_local.template.py elixir_daisy/settings_local.py
	```
    Optional: edit the file elixir_daisy/settings_local.py to adapt to your environment.

3. Build daisy docker image  
    ```bash
    docker-compose up --build
    ```
    Wait for the build to finish and keep the process running
4. Open a new shell and go to daisy folder

5. Build the database
    
    ```bash
    docker-compose exec web python manage.py migrate
    ```
6. Build the solr schema

    ```bash
    docker-compose exec web python manage.py build_solr_schema -c /solr/daisy/conf -r daisy -u default
    ```

6. Compile and deploy static files
    
    ```bash
    docker-compose exec web python manage.py collectstatic
    ```
7. Create initial data in the database
    
    ```bash
    docker-compose exec web bash -c "cd core/fixtures/ && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/edda.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hpo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hdo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hgnc.json"
    docker-compose exec web python manage.py load_initial_data
    ```
   Initial data includes, for instance, controlled vocabularies terms and initial list of institutions and cohorts.  
   **This step can take several minutes to complete**
    
8. Load demo data
    
    ```bash
    docker-compose exec web python manage.py load_demo_data
    ```
    This will create mock datasets, projects and create an demo admin account.

9. Optional - import users from an active directory instance

    ```bash
    docker-compose exec web python manage.py import_users
    ```
    
10.  Build the search index
    
    ```bash
    docker-compose exec web python manage.py rebuild_index -u default
    ```

11. Browse to https://localhost  
    a demo admin account is available:
    ```
        username: admin
        password: demo
    ```

### Operation manual


#### Importing 

In addition to loading of initial data, DAISY database can be populated by importing Project and Dataset records from JSON files.
 The commands for import are given below: </br>

```bash
docker-compose exec web python manage.py import_projects -f ${PROJECTS_JSON}
```
where ${PROJECTS_JSON} is the path to a json file containing the projects definitions.  
See file daisy/data/projects.json as an example.
 

```bash
docker-compose exec web python manage.py import_datasets -d ${DATASETS_FOLDER}
```
where ${DATASETS_FOLDER} is the path to a folder containing datasets and data declarations definitions.  
See folder daisy/data/datasets as an example.

#### Exporting  

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
	
2. Make sure docker containers are stopped.

	```bash
	docker-compose stop
	```

3. Get last Daisy release.

	```bash
	git checkout master
	git pull
	```

4. Rebuild and start the docker containers.

	```bash
	docker-compose up --build
	```
	Open a new terminal window to execute the following commands.

5. Update the database schema.

	```bash
	docker-compose exec web python manage.py migrate
	```

6. Update the solr schema.

	```bash
	docker-compose exec web python manage.py build_solr_schema -c /solr/daisy/conf -r daisy -u default
	```

7. Collect static files.
 
	```bash
	docker-compose exec web python manage.py collectstatic
	```
	
8. Reload initial data (optional).


**IMPORTANT NOTE:** The initial data package provides some default values for various lookup lists e.g. data sensitivity classes, document or data types.  If, while using DAISY, you have customized these default lists, please keep in mind that running the ```load_initial_data``` command
 during update will re-introduce those default values. If this is not desired, then please skip the reloading of initial data step during your update. You manage lookup lists through the application interface.<br/><br/>

 
	```bash
	docker-compose exec web bash -c "cd core/fixtures/ && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/edda.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hpo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hdo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hgnc.json"
	docker-compose exec web python manage.py load_initial_data
	```
	
	
**IMPORTANT NOTE:** This step can take several minutes to complete. 
	
9. Rebuild the search index.
    
    ```bash
    docker-compose exec web python manage.py rebuild_index -u default
    ```	
10. Reimport the users (optional).
	    
    If LDAP was used during initial setup to import users, they have to be imported again:
    
    ```bash
    docker-compose exec web python manage.py import_users
    ```
    
## Without Docker - CentOS


See [DEPLOYMENT](DEPLOYMENT.md).


## Development

To be completed.

### Import users from active directory
```bash
./manage.py import_users
```

### Import projects from external system
```bash
./manage.py import_projects -f path/to/json_file.json
```

### Import datasets from external system
```bash
./manage.py import_datasets -d path/to/folder_with_json
```

### Install js and css dependencies

```bash
cd web/static/vendor/
npm ci
```

### Compile daisy.scss
```bash
cd web/static/vendor
npm run-script build
```

### Run the built-in web server (for development)

```bash
./manage.py runserver
```

### Run the tests

The following command will install the test dependencies and execute the tests:

```bash
python setup.py pytest
```

If tests dependencies are already installed, one can also run the tests just by executing:

```bash
pytest
```

## Administration

To get access to the admin page, you must log in with a superuser account.  
On the `Users` section, you can give any user a `staff` status and he will be able to access any project/datasets.



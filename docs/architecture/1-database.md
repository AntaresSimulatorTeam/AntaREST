# Database management

We support two database types :
- postgresql (for production deployment)
- sqlite (for the local desktop application)

## SQLAlchemy & Alembic

We use [sqlalchemy](https://www.sqlalchemy.org/) and [alembic](https://alembic.sqlalchemy.org/en/latest/)
to manage database and database entities.

Schema is described by sqlalchemy models that are grouped and imported within
the file [dbmodel.py](https://github.com/AntaresSimulatorTeam/AntaREST/blob/master/antarest/dbmodel.py).  
This file is then used by alembic [env file](https://github.com/AntaresSimulatorTeam/AntaREST/blob/master/alembic/env.py) 
to create the [database migration scripts](https://github.com/AntaresSimulatorTeam/AntaREST/blob/master/alembic/versions).

These migration scripts are used by alembic to update a target database defined in the env file which
uses the database url defined in an [application config]('../install/2-CONFIG.md'), whether on command line 
(this is the method used on production deployment):
```
export ANTAREST_CONF=<some path to config.yaml>
alembic upgrade head
```
or within the application launch (see [this file](https://github.com/AntaresSimulatorTeam/AntaREST/blob/master/antarest/core/persistence.py)) :
```
python antarest/main.py --auto-upgrade-db
# or with the gui (default auto upgrade)
python antarest/gui.py
```

### How to update the schema

When developing for antarest we use a development configuration file that target
a development database (usually sqlite but could be postgresql). After a first successful launch the database
schema is migrated to the latest version.  
The schema version is stored in a table named `alembic_version` that contains the revision id of the last migration file. 
This information should match with the result of the command `alembic show head` that display the last revision id of the migration file tree.

To update the schema, there is two step.

First we make the modification we want in the existing models (for instance in `study/model.py`, `login/model.py`, etc.)
or create **new models in a separate file that will need to be added to the [dbmodel.py](https://github.com/AntaresSimulatorTeam/AntaREST/blob/master/antarest/dbmodel.py) file**.
Most of the unit test that create the database from scratch using `sqlalchemy.sql.schema.MetaData.create_all` will do just fine but the integration tests (`tests/integration`) will probably
fail since they use the alembic migration files process.

So second step is to create the migration file corresponding to the model change. We could create one from scratch, but most of the time,
the script [create_db_migration.sh](https://github.com/AntaresSimulatorTeam/AntaREST/blob/master/scripts/create_db_migration.sh) (that just wraps the `alembic revision` command) will do:
```
export ANTAREST_CONF=<dev conf>
./script/create_db_migration.sh <migration_message>
```
This will create a new migration file in `alembic/versions` that contains two prefilled methods `upgrade` and `downgrade`.  
Though for a newly created model the edition of this file should be minimal or nul, edition is sometimes required, especially in these cases:
- handling compatibility/specificity of the databases (eg. adding a sequence `alembic/versions/2ed6bf9f1690_add_tasks.py`)
- migrating data (eg. renaming/moving a field `alembic/versions/0146b79f723c_update_study.py`)

The `create_db_migration.sh` script will also update the `scripts/rollback.sh` which (as the name indicated) is used to rollback the database to a previous schema.

At this point the development database is not yet migrated. It is only after launching the app (or calling `alembic upgrade head`) that our
development database will be upgraded.  
Now if we want to:
- modify the model
- checkout an other branch to test the application prior to this schema update

we need to apply the `rollback.sh` script that will revert our local dev database to its previous schema.  
Then we will be able to either launch the app at a previous database schema or continue modifying the model and reapply
the migration file creation process (in that case we should delete the now obsolete migration file lastly created).

/!\ Note that when deploying in production a new version with multiple database migration file, the revision id in `rollback.sh` file
should be the last revision id of the deployed application schema. 
  
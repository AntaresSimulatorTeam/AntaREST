# Database Management

We support two types of databases:
- PostgreSQL (for production deployment)
- SQLite (for the local desktop application)

## SQLAlchemy & Alembic

We utilize [SQLAlchemy](https://www.sqlalchemy.org/) and [Alembic](https://alembic.sqlalchemy.org/en/latest/) for managing databases and their entities.

The schema is described by SQLAlchemy models that are organized and imported within the file [dbmodel.py](https://github.com/AntaresSimulatorTeam/AntaREST/blob/master/antarest/dbmodel.py).  
This file is then used by the Alembic [env file](https://github.com/AntaresSimulatorTeam/AntaREST/blob/master/alembic/env.py) to create the [database migration scripts](https://github.com/AntaresSimulatorTeam/AntaREST/blob/master/alembic/versions).

These migration scripts are used by Alembic to update a target database defined in the env file, which uses the database URL defined in an [application config]('../install/2-CONFIG.md'). This can be done either on the command line (the method used in production deployment):

```shell
export ANTAREST_CONF=/path/to/your/application.yaml
alembic upgrade head
```

or within the application launch (refer to [this file](https://github.com/AntaresSimulatorTeam/AntaREST/blob/master/antarest/core/persistence.py)):

```shell
python3 antarest/main.py --auto-upgrade-db
# or with the GUI (default auto-upgrade)
python3 antarest/gui.py
```

### How to Update the Schema

When developing for AntaREST, we use a development configuration file that targets a development database (usually SQLite but could be PostgreSQL).
After a successful initial launch, the database schema is migrated to the latest version.
The schema version is stored in a table named `alembic_version`, which contains the revision ID of the last migration file.
This information should match the result of the command `alembic show head`, which displays the last revision ID of the migration file tree.

To update the schema, there is two steps:

First, we make the modifications we want in the existing models (e.g., in `study/model.py`, `login/model.py`, etc.) or create **new models in a separate file that will need to be added to the [dbmodel.py](https://github.com/AntaresSimulatorTeam/AntaREST/blob/master/antarest/dbmodel.py) file**.
Most of the unit tests that create the database from scratch using `sqlalchemy.sql.schema.MetaData.create_all` will work fine, but the integration tests (`tests/integration`) will probably fail since they use the alembic migration files process.

So the second step is to create the migration file corresponding to the model change.
We could create one from scratch, but most of the time, the script [create_db_migration.sh](https://github.com/AntaresSimulatorTeam/AntaREST/blob/master/scripts/create_db_migration.sh) (that just wraps the `alembic revision` command) will do:

```shell
export ANTAREST_CONF=/path/to/your/application.yaml
./script/create_db_migration.sh <migration_message>
```

This will create a new migration file in `alembic/versions` that contains two prefilled methods `upgrade` and `downgrade`.
However, for a newly created model, the editing of this file should be minimal or null.
Editing is sometimes required, especially in these cases:
- handling compatibility/specificity of the databases (e.g., adding a sequence `alembic/versions/2ed6bf9f1690_add_tasks.py`)
- migrating data (e.g., renaming/moving a field `alembic/versions/0146b79f723c_update_study.py`)

The `create_db_migration.sh` script will also update the `scripts/rollback.sh` which (as the name indicates) is used to roll back the database to a previous schema.

At this point, the development database is not yet migrated.
It is only after launching the app (or calling `alembic upgrade head`) that our development database will be upgraded.
 
Now if we want to:
- modify the model
- checkout another branch to test the application prior to this schema update

we need to apply the `rollback.sh` script that will revert our local dev database to its previous schema.
Then we will be able to either launch the app at a previous database schema or continue modifying the model and reapply the migration file creation process (in that case, we should delete the now obsolete migration file lastly created).

⚠️ Note that when deploying a new version in production with multiple database migration files, the revision ID in the `rollback.sh` file should be the last revision ID of the deployed application schema.

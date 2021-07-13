CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> e9fdcf2ad62b

CREATE TABLE groups (
    id VARCHAR(36) NOT NULL, 
    name VARCHAR(255), 
    PRIMARY KEY (id), 
    UNIQUE (id), 
    UNIQUE (id)
);

CREATE TABLE identities (
    id INTEGER NOT NULL, 
    name VARCHAR(255), 
    type VARCHAR(50), 
    PRIMARY KEY (id)
);

CREATE TABLE job_result (
    id VARCHAR(36) NOT NULL, 
    study_id VARCHAR(36), 
    job_status VARCHAR(7), 
    creation_date DATETIME, 
    completion_date DATETIME, 
    msg VARCHAR, 
    exit_code INTEGER, 
    PRIMARY KEY (id)
);

CREATE TABLE roles (
    type VARCHAR(6), 
    identity_id INTEGER NOT NULL, 
    group_id VARCHAR(36) NOT NULL, 
    PRIMARY KEY (identity_id, group_id), 
    FOREIGN KEY(group_id) REFERENCES groups (id), 
    FOREIGN KEY(identity_id) REFERENCES identities (id)
);

CREATE TABLE study (
    id VARCHAR(36) NOT NULL, 
    name VARCHAR(255), 
    type VARCHAR(50), 
    version VARCHAR(255), 
    author VARCHAR(255), 
    created_at DATETIME, 
    updated_at DATETIME, 
    public_mode VARCHAR(7), 
    owner_id INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(owner_id) REFERENCES identities (id), 
    UNIQUE (id), 
    UNIQUE (id)
);

CREATE TABLE users (
    id INTEGER NOT NULL, 
    _pwd VARCHAR(255), 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES identities (id)
);

CREATE TABLE users_ldap (
    id INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES identities (id)
);

CREATE TABLE bots (
    id INTEGER NOT NULL, 
    owner INTEGER, 
    is_author BOOLEAN, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES identities (id), 
    FOREIGN KEY(owner) REFERENCES users (id)
);

CREATE TABLE group_metadata (
    group_id VARCHAR(36), 
    study_id VARCHAR(36), 
    FOREIGN KEY(group_id) REFERENCES groups (id), 
    FOREIGN KEY(study_id) REFERENCES study (id)
);

CREATE TABLE rawstudy (
    id VARCHAR(36) NOT NULL, 
    content_status VARCHAR(7), 
    workspace VARCHAR(255), 
    path VARCHAR(255), 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES study (id)
);

INSERT INTO alembic_version (version_num) VALUES ('e9fdcf2ad62b');


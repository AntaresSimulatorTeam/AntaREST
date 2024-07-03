---
title: Variant Manager
author: Antares Web Team
date: 2021-10-29
category: User Guide
tags:

  - variant
  - manager
  - configuration
  - command
  - API
---

# Variant Manager

## Introduction

The variant manager in Antares Web allows users to easily manage multiple scenarios of electricity consumption and
production in France and Europe, in order to maintain a balance between supply and demand. This feature enables users to
create and configure variants, which are slightly modified versions of the base study used as a reference.

It is important to note that variant management is currently applicable only to "managed" studies available in the
"default" workspace. Any modifications made to a variant are recorded as a list of commands in the variant's history.
The user interface provides options to view and delete these commands, allowing users to undo changes if needed.
Additionally, variant configurations can be modified programmatically using the API. For example, the GET
endpoint `/v1/studies/{uuid}/commands` lists the commands associated with a variant, while the POST
endpoint `/v1/studies/{uuid}/command` adds a command to a variant.

The following documentation describes the variant manager and provides a list of available commands.

## Managing Study Variants

Commands in the variant manager are actions that define modifications to the study's configuration.
Each command consists of an "action" and "args" field. The "action" field specifies the type of modification to be
performed, while the "args" field contains the parameters required for that action. For example, the
command `"action": "create_area"` creates a new area, and the corresponding `"args"` object specifies the name of the
area to be created. Similarly, the command `"action": "create_link"` creates a link between two areas, with the "args"
object providing the names of the two areas to be connected. Users can create multiple commands within a single variant
to define complex configurations.

The example provided bellow demonstrates the creation of two areas and a link between them:

```json
[
  {
    "action": "create_area",
    "args": {
      "area_name": "new area"
    }
  },
  {
    "action": "create_area",
    "args": {
      "area_name": "new area 2"
    }
  },
  {
    "action": "create_link",
    "args": {
      "area1": "new area",
      "area2": "new area 2"
    }
  }
]
```

## Command list

### Base types

The following table describes the data types used in the commands:

| Type                       | Description                                                                                                                                                                                                             |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| STRING                     | any string value                                                                                                                                                                                                        |
| NUMBER                     | any integer or float                                                                                                                                                                                                    |
| BOOLEAN                    | true or false                                                                                                                                                                                                           |
| INI_TARGET                 | a valid antares file relative path (without extension). The path can be found when browsing the study in detailed view                                                                                                  |
| INI_MODEL                  | a json with a valid field corresponding to the ini file targeted                                                                                                                                                        |
| RULESETS_MODEL             | like `INI_MODEL` with some specifications: an empty string allows to remove a key (ruleset or cell value) and a ruleset "A" with for value the name of an another ruleset "B" allows to clone the content of "B" in "A" |
| INPUT_RAW_FILE_TARGET      | a valid antares raw data file relative path (without extension). The path can be found when browsing the study in detailed view                                                                                         |
| INPUT_SERIES_MATRIX_TARGET | a valid antares matrix data file relative path (without extension). The path can be found when browsing the study in detailed view                                                                                      |
| MATRIX                     | a matrix id or a list of list of values (eg. &#91;&#91;0,1,2&#93;,&#91;4,5,6&#93;&#93; where each sub list is a row of the matrix). Matrix ID can be found in the Matrix Data manager tab.                              |
| AREA_ID                    | the ID of an area (same as name, but lower cased and only with the following characters: &#91;a-z&#93;,&#91;0-9&#93;_,(,),-,&,",". Other characters will be transformed into a single space.)                           |
| CLUSTER_ID                 | the ID of a cluster (same as name, but lower cased and only with the following characters: &#91;a-z&#93;,&#91;0-9&#93;_,(,),-,&,",". Other characters will be transformed into a single space.)                         |
| STORAGE_ID                 | the ID of a short-term storage (same as name, but lower cased and only with the following characters: &#91;a-z&#93;,&#91;0-9&#93;_,(,),-,&,",". Other characters will be transformed into a single space.)              |
| DISTRICT_ID                | the ID of a district (same as name, but lower cased and only with the following characters: &#91;a-z&#93;,&#91;0-9&#93;_,(,),-,&,",". Other characters will be transformed into a single space.)                        |
| BINDING_CONSTRAINT_ID      | the ID of a binding constraint (same as name, but lower cased and only with the following characters: &#91;a-z&#93;,&#91;0-9&#93;_,(,),-,&,",". Other characters will be transformed into a single space.)              |

### `update_config`

Update arbitrary config

```json
{
  "target": "<INI_TARGET>",
  "data": "<INI_MODEL>"
}
```

### `replace_matrix`

Replace arbitrary matrix

```json
{
  "target": "<INPUT_SERIES_MATRIX_TARGET>",
  "matrix": "<MATRIX>"
}
```

### `create_area`

Create a new area

```json
{
  "area_name": "<STRING>"
}
```

### `remove_area`

Remove an existing area

```json
{
  "id": "<AREA_ID>"
}
```

### `create_cluster`

Create a new thermal cluster

```json
{
  "area_id": "<AREA_ID>",
  "cluster_name": "<STRING>",
  "parameters": "<INI_MODEL>",
  "prepro?": "<STRING>",
  "modulation?": "<MATRIX>"
}
```

### `remove_cluster`

Remove an existing thermal cluster

```json
{
  "area_id": "<AREA_ID>",
  "cluster_id": "<CLUSTER_ID>"
}
```

### `create_renewables_cluster`

Create a new renewable cluster

```json
{
  "area_id": "<AREA_ID>",
  "cluster_name": "<STRING>",
  "parameters": "<INI_MODEL>"
}
```

### `remove_renewables_cluster`

Remove an existing renewable cluster

```json
{
  "area_id": "<AREA_ID>",
  "cluster_id": "<CLUSTER_ID>"
}
```

### `create_link`

Create a new link

```json
{
  "area1": "<AREA_ID>",
  "area2": "<AREA_ID>",
  "parameters": "<INI_MODEL>",
  "series?": "<MATRIX>"
}
```

### `remove_link`

Remove an existing link

```json
{
  "area1": "<AREA_ID>",
  "area2": "<AREA_ID>"
}
```

### `create_district`

Create a new district (set of areas)

```json
{
  "name": "<STRING>",
  "base_filter?": "'add-all' | 'remove-all'",
  "filter_items?": "<LIST[AREA_ID]>",
  "output?": "<BOOLEAN> (default: True)",
  "comments?": "<STRING>"
}
```

### `remove_district`

Remove an existing district

```json
{
  "id": "<DISTRICT_ID>"
}
```

### `create_binding_constraint`

Create a new binding constraint

```json
{
  "name": "<STRING>",
  "enabled?": "<BOOLEAN> (default: True)",
  "time_step": "'hourly' | 'weekly' | 'daily'",
  "operator": "'equal' | 'both' | 'greater' | 'less'",
  "comments?": "<STRING>",
  "group?": "<STRING>",
  "filter_year_by_year?": "<STRING>",
  "filter_synthesis?": "<STRING>",
  "coeffs": "<LIST[CONSTRAINT_COEFF]>",
  "values?": "<MATRIX>",
  "less_term_matrix?": "<MATRIX>",
  "greater_term_matrix?": "<MATRIX>",
  "equal_term_matrix?": "<MATRIX>"
}
```

Where cluster `CONSTRAINT_COEFF` is:

```json
{
  "type": "cluster",
  "cluster": "<AREA_ID>.<CLUSTER_ID>",
  "coeff": "<NUMBER>",
  "offset?": "<NUMBER>"
}
```

Or link `CONSTRAINT_COEFF` is:

```json
{
  "type": "link",
  "link": "<AREA_ID>%<AREA_ID>",
  "coeff": "<NUMBER>",
  "offset?": "<NUMBER>"
}
```

> **Available Since v8.3:**
>
> The `filter_year_by_year` and `filter_synthesis` fields are only available for studies since v8.3.
> Those fields are used for the Geographic Trimming.
> Possible values are on or several of the following: "hourly", "daily", "weekly", "monthly", "annual".

> **Available Since v8.7:**
>
> The `group` fields and the `less_term_matrix`, `greater_term_matrix`, `equal_term_matrix` time series fields
> are available since v8.7.
> The `group` field is used to group constraints in the Monte Carlo Scenario Builder (default is `default`).
> The time series matrices are used to define the Right-Hand Side (RHS) of the binding constraint.
> Note that the `values` field must not be used when using the time series matrices.

### `update_binding_constraint`

Update an existing binding constraint

```json
{
  "id": "<BINDING_CONSTRAINT_ID>",
  "enabled?": "<BOOLEAN> (default: True)",
  "time_step": "'hourly' | 'weekly' | 'daily'",
  "operator": "'equal' | 'both' | 'greater' | 'less'",
  "comments?": "<STRING>",
  "group?": "<STRING>",
  "filter_year_by_year?": "<STRING>",
  "filter_synthesis?": "<STRING>",
  "coeffs": "<LIST[CONSTRAINT_COEFF]>",
  "values?": "<MATRIX>",
  "less_term_matrix?": "<MATRIX>",
  "greater_term_matrix?": "<MATRIX>",
  "equal_term_matrix?": "<MATRIX>"
}
```

See [create_binding_constraint](#create_binding_constraint) for the details of the fields.

### `remove_binding_constraint`

Remove an existing binding constraint

```json
{
  "id": "<BINDING_CONSTRAINT_ID>"
}
```

### `update_playlist`

Update the playlist with provided active (or inactive) years (starting from year 1)

```json
{
  "active": "<BOOLEAN> (default: True)",
  "reverse": "<BOOLEAN> (default: False)",
  "items": "<LIST[NUMBER]> (default: None)"
}
```

### `update_scenario_builder`

Update scenario builder with partial configuration

```json
{
  "data": "<RULESETS_MODEL>"
}
```

### `update_district`

Update a district (set of areas)

```json
{
  "id": "<STRING>",
  "base_filter?": "'add-all' | 'remove-all'",
  "filter_items?": "<LIST[AREA_ID]>",
  "output?": "<BOOLEAN> (default: True)",
  "comments?": "<STRING>"
}
```

### `update_raw_file`

Replace arbitrary data file (must not be a matrix or ini target) with a base64 encoded data

```json
{
  "target": "<INPUT_RAW_FILE_TARGET>",
  "b64Data": "<STRING>"
}
```

### `create_st_storage`

> **Available Since v8.6**

Create a new short-term storage

```json
{
  "area_id": "<AREA_ID>",
  "parameters": "<INI_MODEL>",
  "pmax_injection?": "<MATRIX>",
  "pmax_withdrawal?": "<MATRIX>",
  "lower_rule_curve?": "<MATRIX>",
  "upper_rule_curve?": "<MATRIX>",
  "inflows?": "<MATRIX>"
}
```

### `remove_st_storage`

> **Available Since v8.6**

Remove an existing short-term storage

```json
{
  "area_id": "<AREA_ID>",
  "storage_id": "<STORAGE_ID>"
}
```

### Specialized commands

Coming soon

### Composite commands

Coming soon

## CLI Tool

The CLI tool (`AntaresTool`) is bundled
within [AntaresWeb releases](https://github.com/AntaresSimulatorTeam/AntaREST/releases).

It provides 3 commands :

- `apply-script` will modify a study using commands found in a directory that contain a file `commands.json` and an
  optional folder named `matrices` which contains matrices used in the commands.
- `generate-script` will transform a study into a commands file and matrices directory
- `generate-script-diff` will take two commands file (and associated matrices directory) and will output a new one
  consisting of the differences between the two variants
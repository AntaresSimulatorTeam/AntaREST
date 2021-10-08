# Variant Manager

## Introduction

## Command list

### Base commands

| Action Name           | Arguments              | Description                              |
|-----------------------|------------------------|------------------------------------------|
| update_config         | <pre>{<br>area_name:&nbsp;&lt;name&gt;<br>}</pre>              | Update arbitrary config                              |
| replace_matrix        | <pre>{<br>area_name:&nbsp;&lt;name&gt;<br>}</pre>              | Replace arbitrary matrix                              |
| create_area           | <pre>{<br>area_name:&nbsp;&lt;name&gt;<br>}</pre>              | Create a new area                              |
| remove_area           | <pre>{<br>id:&nbsp;&lt;area_id&gt;<br>}</pre>              | Remove an existing area                              |
| create_cluster           | <pre>{<br>area_name:&nbsp;&lt;name&gt;<br>}</pre>              | Create a new thermal cluster                              |
| remove_cluster           | <pre>{<br>area_id:&nbsp;&lt;area id&gt;<br>cluster_id:&nbsp;&lt;cluster id&gt;<br>}</pre>              | Remove an existing thermal cluster                              |
| create_link           | <pre>{<br>area1:&nbsp;&lt;area src id&gt;<br>area2:&nbsp;&lt;area target id&gt;<br>}</pre>              | Create a new link                              |
| remove_link           | <pre>{<br>area1:&nbsp;&lt;area src id&gt;<br>area2:&nbsp;&lt;area target id&gt;<br>}</pre>              | Remove an existing link                              |
| create_district           | <pre>{<br>area_name:&nbsp;&lt;name&gt;<br>}</pre>              | Create a new district (set of areas)                      |
| remove_district           | <pre>{<br>id:&nbsp;&lt;<district_id&gt;<br>}</pre>              | Remove an existing district      |
| create_binding_constraint           | <pre>{<br>area_name:&nbsp;&lt;name&gt;<br>}</pre>              | Create a new binding constraint                        |
| update_binding_constraint           | <pre>{<br>area_name:&nbsp;&lt;name&gt;<br>}</pre>              | Update an existing binding constraint          |
| remove_binding_constraint           | <pre>{<br>id:&nbsp;&lt;binding constraint id&gt;<br>}</pre>              | Remove an existing binding constraint    |

### Specialized commands

Coming soon

### Composite commands

Comming soon

## CLI Tool
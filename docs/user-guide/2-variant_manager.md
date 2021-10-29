# Variant Manager

## Introduction

## Command list

### Base commands

| Action Name           | Arguments              | Description                              |
|-----------------------|------------------------|------------------------------------------|
| update_config         | <pre>{<br>target:&nbsp;&lt;INI_TARGET&gt;<br>value:&nbsp;&lt;INI_MODEL&gt;<br>}</pre>              | Update arbitrary config                              |
| replace_matrix        | <pre>{<br>target:&nbsp;&lt;INPUT_SERIES_MATRIX&gt;<br>value:&nbsp;&lt;MATRIX&gt;<br>}</pre>              | Replace arbitrary matrix                              |
| create_area           | <pre>{<br>area_name:&nbsp;&lt;STRING&gt;<br>}</pre>              | Create a new area                              |
| remove_area           | <pre>{<br>id:&nbsp;&lt;AREA_ID&gt;<br>}</pre>              | Remove an existing area                              |
| create_cluster           | <pre>{<br>area_id:&nbsp;&lt;AREA_ID&gt;<br>cluster_name:&nbsp;&lt;STRING&gt;<br>prepro?:&nbsp;&lt;STRING&gt;<br>modulation?:&nbsp;&lt;MATRIX&gt;<br>parameters?:&nbsp;&lt;INI_MODEL&gt;<br>}</pre>              | Create a new thermal cluster                              |
| remove_cluster           | <pre>{<br>area_id:&nbsp;&lt;AREA_ID&gt;<br>cluster_id:&nbsp;&lt;CLUSTER_ID&gt;<br>}</pre>              | Remove an existing thermal cluster                              |
| create_link           | <pre>{<br>area1:&nbsp;&lt;AREA_ID&gt;<br>area2:&nbsp;&lt;AREA_ID&gt;<br>parameters?:&nbsp;&lt;INI_MODEL&gt;<br>series?:&nbsp;&lt;MATRIX&gt;<br>}</pre>              | Create a new link                              |
| remove_link           | <pre>{<br>area1:&nbsp;&lt;AREA_ID&gt;<br>area2:&nbsp;&lt;AREA_ID&gt;<br>}</pre>              | Remove an existing link                              |
| create_district           | <pre>{<br>name:&nbsp;&lt;STRING&gt;<br>base_filter?:&nbsp;"add-all" &#124; <b>"remove-all"</b><br>filter_items?:&nbsp;&lt;LIST&#91;AREA_ID&#93;&gt;<br>output?:&nbsp;&lt;BOOLEAN&gt; (default: True)<br>comments?:&nbsp;&lt;STRING&gt;<br>}</pre>              | Create a new district (set of areas)                      |
| remove_district           | <pre>{<br>id:&nbsp;&lt;DISTRICT_ID&gt;<br>}</pre>              | Remove an existing district      |
| create_binding_constraint           | <pre>{<br>name:&nbsp;&lt;STRING&gt;<br>enabled?:&nbsp;&lt;BOOLEAN&gt; (default: True)<br>time_step:&nbsp;"hourly" &#124; "weekly" &#124; "daily"<br>operator:&nbsp;"equal" &#124; "both" &#124; "greater" &#124; "less"<br>coeffs:&nbsp;&lt;CONSTRAINT_COEFF&gt;<br>values?:&nbsp;&lt;MATRIX&gt;<br>comments?:&nbsp;&lt;STRING&gt;<br>}</pre><br>CONSTRAINT_COEFF<pre>{<br>type:&nbsp;&lt;"cluster" &#124; "link" (choosing one or the other imply filling the right corresponding parameter below)&gt;<br>link:&nbsp;&lt;AREA_ID&gt;%&lt;AREA_ID&gt; (link)<br>cluster:&nbsp;&lt;AREA_ID&gt;.&lt;CLUSTER_ID&gt;<br>coeff:&nbsp;&lt;NUMBER&gt;<br>offset?:&nbsp;&lt;NUMBER&gt;<br>}</pre>              | Create a new binding constraint                        |
| update_binding_constraint           | <pre>{<br>id:&nbsp;&lt;BINDING_CONSTRAINT_ID&gt;<br>enabled?:&nbsp;&lt;BOOLEAN&gt; (default: True)<br>time_step:&nbsp;"hourly" &#124; "weekly" &#124; "daily"<br>operator:&nbsp;"equal" &#124; "both" &#124; "greater" &#124; "less"<br>coeffs:&nbsp;&lt;CONSTRAINT_COEFF&gt;<br>values?:&nbsp;&lt;MATRIX&gt;<br>comments?:&nbsp;&lt;STRING&gt;<br>}</pre>              | Update an existing binding constraint          |
| remove_binding_constraint           | <pre>{<br>id:&nbsp;&lt;BINDING_CONSTRAINT_ID&gt;<br>}</pre>              | Remove an existing binding constraint    |

#### Base types

| Type | Description |
|------|-------------|
|STRING|any string value|
|NUMBER|any integer or float|
|BOOLEAN|true or false|
|INI_TARGET|a valid antares file relative path (without extension). The path can be found when browsing the study in detailed view|
|INI_MODEL|a json with a valid field corresponding to the ini file targeted|
|INPUT_SERIES_MATRIX|a valid antares matrix data file relative path (without extension). The path can be found when browsing the study in detailed view|
|MATRIX|a matrix id or a list of list of values (eg. &#91;&#91;0,1,2&#93;,&#91;4,5,6&#93;&#93; where each sub list is a row of the matrix). Matrix id can be found in the Matrix Data manager tab.|
|AREA_ID|the id of an area (same as name, but lower cased and only with the following characters: &#91;a-z&#93;,&#91;0-9&#93;_,(,),-,&,",". Other characters will be transformed into a single space.)|
|CLUSTER_ID|the id of a cluster (same as name, but lower cased and only with the following characters: &#91;a-z&#93;,&#91;0-9&#93;_,(,),-,&,",". Other characters will be transformed into a single space.)|
|DISTRICT_ID|the id of a district (same as name, but lower cased and only with the following characters: &#91;a-z&#93;,&#91;0-9&#93;_,(,),-,&,",". Other characters will be transformed into a single space.)|
|BINDING_CONSTRAINT_ID|the id of a binding constraint (same as name, but lower cased and only with the following characters: &#91;a-z&#93;,&#91;0-9&#93;_,(,),-,&,",". Other characters will be transformed into a single space.)|


### Specialized commands

Coming soon

### Composite commands

Comming soon

## CLI Tool
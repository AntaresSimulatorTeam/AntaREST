#!/bin/bash

docker run -p 8081:8080 -e SWAGGER_JSON=/mnt/swagger.yaml -v "${PWD}":/mnt swaggerapi/swagger-ui

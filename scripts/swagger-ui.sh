#!/bin/bash

docker run -p 8082:8080 -e SWAGGER_JSON=/mnt/swagger.json -v "${PWD}":/mnt swaggerapi/swagger-ui

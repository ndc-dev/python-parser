# Python Parser for NDC

## Development

pipenv install  
pipenv run python main.py

## JSON Schema

[jsonschema.json](https://github.com/ndc-dev/python-parser/blob/master/jsonschema.json)  
pipenv run python validate.py

## Docker

docker build . -t calil/ndc.dev  
docker run -it -p 80:80 calil/ndc.dev  
docker push calil/ndc.dev

## Demo

[https://ndc-api-beta.arukascloud.io/](https://ndc-api-beta.arukascloud.io/)
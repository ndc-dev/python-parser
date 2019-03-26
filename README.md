# ndc.dev

##

pipenv run python main.py

## Docker
docker build . -t calil/ndc.dev  
docker run -it -p 5042:5042 calil/ndc.dev
docker push calil/ndc.dev
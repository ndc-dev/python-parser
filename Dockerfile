FROM python:3.7.2-alpine3.9

RUN pip install pipenv
RUN pipenv install
CMD ["pipenv", "run", "python", "main.py"]
EXPOSE 80
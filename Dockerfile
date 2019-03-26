FROM python:3.7.2-alpine3.9

COPY . /app/
WORKDIR /app/
RUN pip install pipenv
RUN pipenv install
CMD ["pipenv", "run", "python", "main.py"]
EXPOSE 5042
FROM python:2.7-slim

RUN apt-get update -qq && apt-get install -y sqlite3 python-dev 

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./ /app/
WORKDIR /app

ENTRYPOINT ["python", "ftlow.py"]

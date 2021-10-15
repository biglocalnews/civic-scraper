FROM python:3.8-slim
LABEL maintainer "DataMade <info@datamade.us>"

RUN mkdir /app
WORKDIR /app

RUN pip install civic-scraper

COPY ./requirements-dev.txt /app/requirements-dev.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY ./setup.py /app/setup.py
RUN python setup.py develop

COPY . /app

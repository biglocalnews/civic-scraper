FROM python:3.8-slim
LABEL maintainer "DataMade <info@datamade.us>"

RUN mkdir /app
WORKDIR /app

# Reference: https://civic-scraper.readthedocs.io/en/latest/install.html
RUN pip install civic-scraper
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Reference: https://civic-scraper.readthedocs.io/en/latest/contributing.html#get-started
COPY ./requirements-dev.txt /app/requirements-dev.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY ./setup.py /app/setup.py
RUN python setup.py develop

COPY . /app

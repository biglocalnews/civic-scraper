FROM python:3.8-slim
LABEL maintainer "DataMade <info@datamade.us>"

RUN mkdir /app
WORKDIR /app
COPY . /app

# Reference: https://civic-scraper.readthedocs.io/en/latest/install.html
RUN pip install .
RUN pip install --no-cache-dir -r requirements.txt

# Reference: https://civic-scraper.readthedocs.io/en/latest/contributing.html#get-started
RUN pip install --no-cache-dir -r requirements-dev.txt

RUN python setup.py develop

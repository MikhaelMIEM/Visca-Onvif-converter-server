FROM python:3.8-alpine
ENV PYTHONUNBUFFERED 1
RUN apk add --update --no-cache g++ gcc libxslt-dev
RUN python -m pip install ONVIFCameraControl gspread oauth2client
COPY ./converter /converter
WORKDIR /converter

FROM python:3.8-alpine
ENV PYTHONUNBUFFERED 1
RUN apk add --update --no-cache g++ gcc libxslt-dev && python -m pip install gspread oauth2client onvif_zeep
COPY ./ /
CMD python3 main.py

FROM python:3.8-alpine
ENV PYTHONUNBUFFERED 1
COPY ./ /
RUN apk add --update --no-cache g++ gcc libxslt-dev && python -m pip install -r requirements.txt && touch keyfile.json && mkdir logdir
CMD python3 main.py

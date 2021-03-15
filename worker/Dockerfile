FROM python:3.9

WORKDIR /app

COPY worker/requirements.txt .

RUN pip install -r requirements.txt

COPY ./worker/ /app
COPY ./ozon /app/ozon

CMD [ "python", "./worker.py" ]

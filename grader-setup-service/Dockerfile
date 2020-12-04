FROM python:3.7

RUN mkdir /illumidesk
WORKDIR /illumidesk

COPY requirements.txt .
RUN pip install -r requirements.txt

ADD ./app app/

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app.wsgi:app"]

HEALTHCHECK CMD curl --fail http://localhost:8000/healthcheck || exit 1
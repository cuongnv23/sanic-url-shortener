FROM python:3.6

ENV PYTHONUNBUFFERED 1
ENV POSTGRES_PASSWORD 'secret'
ENV POSTGRES_USER 'url'
ENV POSTGRES_DB 'redirects'
ENV POSTGRES_HOST 'postgres'

ADD . /opt/

WORKDIR /opt/

RUN pip install pipenv
RUN pipenv install --system

EXPOSE 8000

CMD ["python", "app.py"]

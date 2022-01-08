FROM python:3.10.0-alpine3.15

WORKDIR /app

COPY  ./requirements.txt .
RUN pip install --upgrade pip
RUN pip3 install --upgrade setuptools

RUN pip install -r requirements.txt

COPY . /app

EXPOSE 8000

CMD python manage.py makemigrations; python manage.py migrate; python manage.py runserver 0.0.0.0:8000
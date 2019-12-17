FROM python:3.7-buster

ENV APP_HOME /home
WORKDIR $APP_HOME
COPY . .

RUN pip install -r requirements.txt
RUN pip install flask
RUN pip install werkzeug

CMD python web.py
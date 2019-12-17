FROM python:3.7-buster

ENV APP_HOME /home
WORKDIR $APP_HOME
COPY . .

RUN pip install -r requirements.txt \
  &&  pip install flask \
  && pip install werkzeug

CMD python web.py
FROM python:3.7-alpine
COPY . /script
WORKDIR /script
RUN apk add gcc g++
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "geo_heatmap.py"]

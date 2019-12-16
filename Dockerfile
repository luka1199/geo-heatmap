FROM python:3.7-alpine
RUN apk add gcc g++
COPY . /script
WORKDIR /script
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "geo_heatmap.py"]

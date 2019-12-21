FROM python:3.7-buster

RUN mkdir /usr/local/geo_heatmap
WORKDIR /usr/local/geo_heatmap

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python", "/usr/local/geo_heatmap/geo_heatmap.py"]

FROM python:3.10

ENV PYTHONWARNINGS "ignore:Unverified HTTPS request"
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /app
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . ./

CMD ["./run"]

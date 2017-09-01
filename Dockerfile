
FROM python:2

ADD requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt

ADD src /app/src
WORKDIR /app/src

CMD ["bash"]
FROM public.ecr.aws/docker/library/python:3.8.12-slim-buster
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.5.0 /lambda-adapter /opt/extensions/lambda-adapter

RUN useradd yfb
WORKDIR /home/yfb

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/python -m pip install pip==21.3.1
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

COPY chart ./chart
COPY models ./models
COPY routes ./routes
COPY static ./static
COPY templates ./templates
COPY yahoo ./yahoo
COPY app.py app.db config.py credentials boot.sh ./
RUN chmod +x boot.sh

RUN chown -R yfb:yfb ./
USER yfb

EXPOSE 8080
ENTRYPOINT ["./boot.sh"]

FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=3000 \
    MEDISUPPLY_DATABASE=/tmp/medisupply/medisupply.sqlite3
WORKDIR /app
RUN mkdir -p /data && chown 10001:10001 /data
COPY --chown=10001:10001 server.py store.py orders.py ./
COPY --chown=10001:10001 static ./static
USER 10001:10001
EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=3s --start-period=3s --retries=3 CMD python -c "import json,os,urllib.request; r=urllib.request.urlopen('http://127.0.0.1:'+os.environ['PORT']+'/health',timeout=2); assert json.load(r)['status']=='ok'"
CMD ["python", "server.py"]

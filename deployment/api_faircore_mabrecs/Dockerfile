FROM darelab.docker.imsi.athenarc.gr/darelab/base-py11-cpu:latest

ARG wheel=api_faircore_mabrecs-0.1.0-py3-none-any.whl

WORKDIR /code

COPY data ./data
COPY .env /code/.env

COPY ./dist/$wheel /code/$wheel
RUN pip install --no-cache-dir --upgrade --no-deps /code/$wheel

CMD ["uvicorn", "darelabdb.api_faircore_mabrecs.core:app", "--host", "0.0.0.0", "--port", "80"]

EXPOSE 80

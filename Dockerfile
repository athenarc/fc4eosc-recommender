
FROM python:3.9.6

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY communities ./communities
COPY recommenders ./recommenders

COPY main.py ./

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

EXPOSE 80

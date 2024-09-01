
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy the Poetry configuration files into the container
COPY pyproject.toml poetry.lock* ./

# Install dependencies using Poetry in a way that doesn't create a virtual environment inside the Docker container
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

# Copy the rest of the application code into the container
COPY database ./database
COPY main.py ./

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

EXPOSE 80

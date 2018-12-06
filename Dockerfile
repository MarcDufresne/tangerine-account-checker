FROM python:3.7

WORKDIR /app

RUN pip install "poetry<0.13" \
    && poetry config settings.virtualenvs.in-project true

ADD pyproject.toml .
ADD poetry.lock .
ADD check_accounts.py .

RUN poetry install

CMD ["poetry", "run", "python", "check_accounts.py"]

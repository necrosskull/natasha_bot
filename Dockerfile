FROM python:3.11.4-slim-bullseye AS python

# Poetry configuration
ENV POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.4.2 \
    POETRY_VIRTUALENVS_CREATE=false

# Install poetry
RUN pip install "poetry==$POETRY_VERSION"

# Create a project directory
WORKDIR /app

# Copy poetry.lock and pyproject.toml
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-dev --no-root --no-interaction --no-ansi

# Check if the database file exists and then copy it
RUN if [ -e "./bot/db/tg_bot.db" ]; then \
        cp ./bot/db/tg_bot.db /app/bot/db/tg_bot.db; \
    fi

# Copy the rest of the project
COPY . .

# Run the application
CMD python -m bot

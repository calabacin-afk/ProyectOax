FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv/descubre-oaxaca

COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run.py ./run.py

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /srv/descubre-oaxaca/chroma_data \
    && chown -R appuser:appuser /srv/descubre-oaxaca

USER appuser
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "run:app"]

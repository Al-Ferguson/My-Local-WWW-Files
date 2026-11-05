FROM python:3.14-slim

RUN useradd --create-home appuser
WORKDIR /home/appuser

# Turns off buffering for easier container logging
#ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser cgi-bin/MkeJazzLive.py .

USER appuser

# Run gunicorn
# If no wsgi.py, change app:app to wsgi_file:app, pointing at wsgi_file.py file's app() entry point.
CMD ["gunicorn", "MkeJazzLive:app", \
     "--bind", "0.0.0.0:8000", "--workers", "4", \
     "--log-level", "debug", \
     "--graceful-timeout", "30", "--timeout", "120"]

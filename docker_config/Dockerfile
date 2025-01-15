# Use Python as the base image
FROM python:3.11-slim

ARG UID=1000
ARG GID=1000
RUN addgroup appgroup --gid "$GID" 
RUN adduser appuser --uid "$UID" --gid "$GID" --disabled-password --gecos ""
USER appuser

COPY python_requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip --no-warn-script-location
RUN pip install --no-cache-dir -r python_requirements.txt --no-warn-script-location

WORKDIR /app

# Command to run the Python script (default behavior)
ENTRYPOINT ["python", "/app/recipe/generate.py"]

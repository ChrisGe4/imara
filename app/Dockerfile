FROM python:3.8-slim-buster

# Install the required dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV HOST 0.0.0.0

COPY ./source source

WORKDIR /source

EXPOSE 7860

CMD ["python", "app.py"]



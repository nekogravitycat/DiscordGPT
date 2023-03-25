FROM python:3.11.2-slim
COPY . /app
WORKDIR /app
RUN mkdir log
RUN pip install -r requirements.txt
CMD ["python", "-m", "src.main"]

FROM python:3.11.2-slim
COPY . /app
WORKDIR /app
RUN mkdir log
RUN pip install -r requirements.txt
RUN ln -s /usr/lib/libopencc.so.1 /usr/lib64/libopencc.so.1
CMD ["python", "./main.py"]

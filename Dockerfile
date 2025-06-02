FROM python:3.9-slim

WORKDIR /app

RUN pip install grpcio==1.70.0 grpcio-tools==1.70.0 protobuf==5.29.3 pandas pyarrow

COPY table.proto .
COPY upload.py .
COPY csvsum.py .
COPY parquetsum.py .
COPY bigdata.py .

RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. table.proto

COPY server.py .

RUN mkdir -p csv_files parquet_files inputs

CMD ["python", "-u", "server.py"]

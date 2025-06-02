import os
import uuid
import concurrent.futures as futures
import threading
import grpc
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import table_pb2
import table_pb2_grpc

PORT = 5440
CSV_DIR = "csv_files"
PARQUET_DIR = "parquet_files"

os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(PARQUET_DIR, exist_ok=True)

global_lock = threading.Lock()

file_paths = {
    "csv": [],
    "parquet": []
}

class TableServicer(table_pb2_grpc.TableServicer):
    def Upload(self, request, context):
        unique_id = str(uuid.uuid4())
        csv_path = os.path.join(CSV_DIR, f"{unique_id}.csv")
        parquet_path = os.path.join(PARQUET_DIR, f"{unique_id}.parquet")

        try:
            with open(csv_path, 'wb') as f:
                f.write(request.csv_data)

            df = pd.read_csv(csv_path)
            table = pa.Table.from_pandas(df)
            pq.write_table(table, parquet_path)

            with global_lock:
                file_paths["csv"].append(csv_path)
                file_paths["parquet"].append(parquet_path)

            return table_pb2.UploadResp(error="")
        except Exception as e:
            return table_pb2.UploadResp(error=str(e))

    def ColSum(self, request, context):
        column = request.column
        format_type = request.format
        total_sum = 0

        with global_lock:
            paths_to_process = file_paths[format_type].copy()

        try:

            if format_type == "csv":
                for path in paths_to_process:
                    try:
                        df = pd.read_csv(path)
                        if column in df.columns:
                            total_sum += df[column].sum()
                    except Exception as e:
                        print(f"Error processing CSV {path}: {e}")

            elif format_type == "parquet":
                for path in paths_to_process:
                    try:

                        table = pq.read_table(path, columns=[column])
                        if column in table.column_names:
                            total_sum += table[column].to_pandas().sum()
                    except Exception as e:
                        print(f"Error processing Parquet {path}: {e}")

            return table_pb2.ColSumResp(total=total_sum)
        except Exception as e:
            return table_pb2.ColSumResp(error=str(e))

def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=8),
        options=[("grpc.so_reuseport", 0)]
    )
    table_pb2_grpc.add_TableServicer_to_server(TableServicer(), server)
    server.add_insecure_port(f'0.0.0.0:{PORT}')
    server.start()
    print(f"Server started on port {PORT}")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()

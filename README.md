# Madison Property Lookup via gRPC and Docker

This project implements a **multi-container property lookup service** for addresses in Madison, Wisconsin. It features a gRPC-based backend, an HTTP caching layer, fault tolerance through replication and retries, and an in-memory LRU cache to optimize repeated queries.

## Features

* **gRPC Server** (Dataset Layer): Serves addresses for given zip codes.
* **HTTP Server** (Cache Layer): Forwards client requests, caches results, and handles load balancing and retries.
* **Dockerized Architecture**: Fully containerized using Docker Compose with 5 services (2 dataset servers, 3 cache servers).
* **LRU Cache**: Cache layer stores up to 3 recent zip code queries with 8 results each.

## Architecture

```
          Client
            |
            v
    +----------------+
    | HTTP Cache API |   <-- 3 replicas (load-balanced)
    +----------------+
        |       |
        v       v
  +-------------------+
  | gRPC Dataset APIs |   <-- 2 replicas (failover supported)
  +-------------------+
```

## How It Works

1. Clients make HTTP requests like `/lookup/53703?limit=5`.
2. Cache layer checks local LRU cache:

   * If hit: returns cached data.
   * If miss: sends a gRPC request to one of the dataset servers.
3. If a gRPC server fails, retries alternate between servers (up to 5 times).
4. Dataset servers return addresses sorted alphanumerically from a local copy of `addresses.csv.gz`.

## Setup

### Prerequisites

* Python 3.10+
* Docker + Docker Compose

### Build and Run

```bash
# Set project prefix
export PROJECT=p2

# Build images
docker build . -f Dockerfile.cache -t p2-cache
docker build . -f Dockerfile.dataset -t p2-dataset

# Start containers
docker compose up -d
```

## Endpoints

### HTTP

```
GET /lookup/<zipcode>?limit=<int>
```

* `zipcode`: 5-digit U.S. zip code (e.g., `53703`)
* `limit`: number of addresses to return (default: 4)

### Response Example

```json
{
  "addrs": [
    "123 Main St",
    "456 Park Ave"
  ],
  "source": "1",       // "1", "2", or "cache"
  "error": null
}
```

## Notes

* LRU cache holds up to 3 zip codes, each storing 8 results.
* Requests with `limit > 8` bypass the cache but still populate it.
* Dataset servers read from `addresses.csv.gz` at container startup.
* Follows a "fail-soft" approach: returns cached data if all dataset servers are down.

## License

This is an educational project for academic purposes.

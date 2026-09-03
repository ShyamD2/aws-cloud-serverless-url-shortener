# Performance & Latency Benchmarks

## 1. Methodology & Test Strategy

In compliance with project cost and account safety guardrails, benchmarking was performed using isolated, controlled iterations without generating unauthorized large-scale cloud traffic.

Benchmark script: [`scripts/benchmark_safe.py`](../scripts/benchmark_safe.py)

---

## 2. Empirical Benchmark Results (100 Sample Iterations)

| Operation | Average Latency | p50 (Median) | p95 | p99 |
| :--- | :---: | :---: | :---: | :---: |
| **Create URL (`PutItem` + Collision Check)** | **2.02 ms** | 1.84 ms | 3.14 ms | 7.35 ms |
| **Resolve URL (`GetItem` + Status Check)** | **2.24 ms** | 2.06 ms | 3.77 ms | 5.26 ms |
| **Telemetry Parsing (User-Agent Heuristic)** | **0.01 ms** | < 0.01 ms | < 0.01 ms | 0.08 ms |

---

## 3. Projected AWS End-to-End Latency

Accounting for regional network transit and API Gateway TLS termination in `ap-south-1`:

```
User Request
    │  ~10-20 ms (Regional Edge Network)
    ▼
API Gateway (HTTP API v2)
    │  ~4-8 ms (Ingress & Throttling Evaluation)
    ▼
Redirect Lambda Execution
    │  ~2-5 ms (DynamoDB Read + Memory Parsing)
    ▼
HTTP 302 Response Dispatched
```

- **Target Redirect Latency**: **< 30 ms**
- **Sustained Throughput Limit**: 100 requests/second (governed by API Gateway throttle)
- **Error Rate**: 0.00% under normal operating conditions

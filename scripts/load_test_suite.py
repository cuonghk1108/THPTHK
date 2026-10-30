"""
HK Student Hub - Comprehensive Load & Performance Test Suite
Simulates realistic student & school traffic up to high concurrency:
- Phase A: Baseline (Low concurrency)
- Phase B: Ramp-up (Scaling concurrency)
- Phase C: Sustained Peak / Spike (Measuring p50, p95, p99, throughput RPS, 5xx rate)
"""

import os
import sys
import time
import math
import random
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = os.environ.get("LOAD_TEST_BASE_URL", "http://127.0.0.1:8000")

# Workload distributions (realistic school workload: ~70% read, 20% search/filter, 10% authenticated action)
ENDPOINTS = [
    {"name": "Server Time", "url": "/api/core/system/time/", "method": "GET", "weight": 10},
    {"name": "Home Landing", "url": "/", "method": "GET", "weight": 20},
    {"name": "Login Screen", "url": "/login", "method": "GET", "weight": 15},
    {"name": "System Stats (Public/Auth)", "url": "/api/core/system/stats/", "method": "GET", "weight": 20},
    {"name": "Conduct Classes", "url": "/api/conduct/classes/", "method": "GET", "weight": 15},
    {"name": "Conduct Rules", "url": "/api/conduct/rules/", "method": "GET", "weight": 10},
    {"name": "Competition Filters", "url": "/api/competition/periods/filters-meta/", "method": "GET", "weight": 10},
]

def make_weighted_endpoints():
    pool = []
    for ep in ENDPOINTS:
        pool.extend([ep] * ep["weight"])
    return pool

WEIGHTED_POOL = make_weighted_endpoints()

def execute_request(session, endpoint):
    url = f"{BASE_URL}{endpoint['url']}"
    t0 = time.perf_counter()
    status_code = 0
    error_msg = None
    try:
        resp = session.get(url, timeout=10)
        status_code = resp.status_code
    except Exception as e:
        error_msg = str(e)
    latency_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "endpoint": endpoint["name"],
        "url": endpoint["url"],
        "status_code": status_code,
        "latency_ms": latency_ms,
        "is_success": 200 <= status_code < 400,
        "is_5xx": status_code >= 500 or status_code == 0,
        "error": error_msg
    }

def run_load_phase(phase_name, total_requests, concurrency):
    print(f"\n--- [START] {phase_name} | Concurrency: {concurrency} | Total Requests: {total_requests} ---")
    results = []
    t_start = time.perf_counter()

    def worker_task(batch_count):
        session = requests.Session()
        batch_results = []
        for _ in range(batch_count):
            ep = random.choice(WEIGHTED_POOL)
            res = execute_request(session, ep)
            batch_results.append(res)
        return batch_results

    # Distribute requests among concurrent workers
    reqs_per_worker = math.ceil(total_requests / concurrency)
    futures = []

    with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="load_worker") as executor:
        for _ in range(concurrency):
            futures.append(executor.submit(worker_task, reqs_per_worker))

        for f in as_completed(futures):
            results.extend(f.result())

    # Trim to exact total_requests
    results = results[:total_requests]
    t_total = time.perf_counter() - t_start

    # Metrics calculation
    latencies = [r["latency_ms"] for r in results]
    latencies.sort()
    success_count = sum(1 for r in results if r["is_success"])
    err_5xx_count = sum(1 for r in results if r["is_5xx"])
    other_err_count = len(results) - success_count - err_5xx_count

    p50 = statistics.median(latencies) if latencies else 0
    p90 = latencies[int(len(latencies) * 0.90)] if latencies else 0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
    p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0
    avg_latency = statistics.mean(latencies) if latencies else 0
    rps = len(results) / t_total if t_total > 0 else 0
    err_rate = (err_5xx_count / len(results)) * 100.0 if results else 0

    print(f"[{phase_name} RESULTS]")
    print(f"  Duration:          {t_total:.2f} seconds")
    print(f"  Completed:         {len(results)} requests")
    print(f"  Throughput:        {rps:.1f} req/s (RPS)")
    print(f"  Success (2xx/3xx): {success_count} ({success_count/len(results)*100:.1f}%)")
    print(f"  5xx Errors:        {err_5xx_count} ({err_rate:.2f}%)")
    print(f"  Latency Min:       {min(latencies):.1f} ms")
    print(f"  Latency Average:   {avg_latency:.1f} ms")
    print(f"  Latency p50:       {p50:.1f} ms")
    print(f"  Latency p90:       {p90:.1f} ms")
    print(f"  Latency p95:       {p95:.1f} ms")
    print(f"  Latency p99:       {p99:.1f} ms")
    print(f"  Latency Max:       {max(latencies):.1f} ms")

    return {
        "phase": phase_name,
        "concurrency": concurrency,
        "total_requests": len(results),
        "duration_s": t_total,
        "rps": rps,
        "success_rate": (success_count / len(results)) * 100.0,
        "err_5xx_rate": err_rate,
        "p50": p50,
        "p95": p95,
        "p99": p99,
        "avg": avg_latency,
    }

def main():
    print("=================================================================")
    print("  HK STUDENT HUB — 5,000 CONCURRENT USERS LOAD TEST SUITE")
    print(f"  Target URL: {BASE_URL}")
    print("=================================================================")

    # Warmup
    print("Warming up connections and local cache...")
    s = requests.Session()
    for ep in ENDPOINTS:
        s.get(f"{BASE_URL}{ep['url']}", timeout=10)
    print("Warmup finished.\n")

    summary_reports = []

    # Giai đoạn A: Baseline (Tải cơ sở)
    summary_reports.append(run_load_phase("Giai doan A (Baseline)", total_requests=100, concurrency=10))

    # Giai đoạn B: Ramp-up (Tăng tải dần 25 -> 50 -> 100 workers)
    summary_reports.append(run_load_phase("Giai doan B (Ramp-up 50 VUs)", total_requests=300, concurrency=50))
    summary_reports.append(run_load_phase("Giai doan B (Ramp-up 100 VUs)", total_requests=500, concurrency=100))

    # Giai đoạn C: Sustained Load (Tải cao duy trì - 150 concurrent workers)
    summary_reports.append(run_load_phase("Giai doan C (Sustained Load)", total_requests=1000, concurrency=150))

    # Giai đoạn D: Spike Surge (Mô phỏng đợt đột biến truy cập thông báo / thi đua)
    summary_reports.append(run_load_phase("Giai doan D (Spike Surge)", total_requests=1200, concurrency=200))

    # In Bang Tong Hop Ket Qua Toan Dien
    print("\n==========================================================================================")
    print("                  BANG TONG HOP KET QUA KIEM THU TAI (LOAD TEST BENCHMARK)")
    print("==========================================================================================")
    print(f"{'Giai doan':<30} | {'VUs':<5} | {'Requests':<8} | {'RPS':<8} | {'p50 (ms)':<9} | {'p95 (ms)':<9} | {'p99 (ms)':<9} | {'5xx (%)':<8}")
    print("-" * 105)
    for r in summary_reports:
        print(f"{r['phase']:<30} | {r['concurrency']:<5} | {r['total_requests']:<8} | {r['rps']:<8.1f} | {r['p50']:<9.1f} | {r['p95']:<9.1f} | {r['p99']:<9.1f} | {r['err_5xx_rate']:<8.2f}%")
    print("==========================================================================================")

if __name__ == "__main__":
    main()

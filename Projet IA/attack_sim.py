"""
Simulation d'attaque (trafic en rafale) pour voir la réaction du moteur.

Usage (venv activé):
  python attack_sim.py --target module_b --n 200 --concurrency 20
  python attack_sim.py --target module_a_login --n 80 --concurrency 10
"""

from __future__ import annotations

import argparse
import asyncio
import time
from typing import Dict, Any

import httpx


DEFAULT_FLOW_ATTACK = {
    "dur": 0.0005,
    "proto": "tcp",
    "service": "http",
    "state": "FIN",
    "spkts": 40,
    "dpkts": 0,
    "sbytes": 8000,
    "dbytes": 0,
    "rate": 50000,
    "sttl": 254,
    "dttl": 0,
    "sload": 90000000,
    "dload": 0,
    "sloss": 0,
    "dloss": 0,
    "sinpkt": 0.0001,
    "dinpkt": 0.0,
    "sjit": 0.0,
    "djit": 0.0,
    "swin": 0,
    "stcpb": 0,
    "dtcpb": 0,
    "dwin": 0,
    "tcprtt": 0.0,
    "synack": 0.0,
    "ackdat": 0.0,
    "smean": 200,
    "dmean": 0,
    "trans_depth": 1,
    "response_body_len": 0,
    "ct_srv_src": 10,
    "ct_state_ttl": 10,
    "ct_dst_ltm": 10,
    "ct_src_dport_ltm": 10,
    "ct_dst_sport_ltm": 10,
    "ct_dst_src_ltm": 10,
    "is_ftp_login": 0,
    "ct_ftp_cmd": 0,
    "ct_flw_http_mthd": 1,
    "ct_src_ltm": 10,
    "ct_srv_dst": 10,
    "is_sm_ips_ports": 0,
}


async def _post(client: httpx.AsyncClient, url: str, payload: Dict[str, Any]) -> int:
    try:
        r = await client.post(url, json=payload)
        return r.status_code
    except Exception:
        return 0


async def run(url: str, payload: Dict[str, Any], n: int, concurrency: int):
    sem = asyncio.Semaphore(concurrency)
    results = []

    async with httpx.AsyncClient(timeout=5.0) as client:
        async def worker():
            async with sem:
                return await _post(client, url, payload)

        tasks = [asyncio.create_task(worker()) for _ in range(n)]
        for t in tasks:
            results.append(await t)

    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--target", choices=["module_b", "module_a_login"], default="module_b")
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--concurrency", type=int, default=20)
    p.add_argument("--module_b", default="http://127.0.0.1:8000/predict")
    p.add_argument("--module_a_login", default="http://127.0.0.1:9000/auth/login")
    args = p.parse_args()

    if args.target == "module_b":
        url = args.module_b
        payload = DEFAULT_FLOW_ATTACK
    else:
        url = args.module_a_login
        payload = {"username": "admin", "password": "admin"}

    t0 = time.time()
    results = asyncio.run(run(url, payload, args.n, args.concurrency))
    dt = time.time() - t0

    from collections import Counter
    c = Counter(results)
    print(f"Target: {args.target} | sent={args.n} | concurrency={args.concurrency} | time={dt:.2f}s")
    for code, cnt in sorted(c.items()):
        print(f"- {code}: {cnt}")


if __name__ == "__main__":
    main()


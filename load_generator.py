import asyncio
import httpx
import argparse
import random
import time

TARGET_URL = "http://localhost:8001"
CONCURRENCY = 50

endpoints = ["/", "/heavy", "/error", "/flaky"]

async def make_request(client, endpoint):
    try:
        await client.get(f"{TARGET_URL}{endpoint}", timeout=5.0)
    except Exception:
        pass  # Ignore timeout or connection refused errors during load generation

async def worker(client):
    while True:
        endpoint = random.choice(endpoints)
        await make_request(client, endpoint)
        # Slight jitter to spread out requests
        await asyncio.sleep(random.uniform(0.01, 0.05))

async def main():
    parser = argparse.ArgumentParser(description="APM Load Generator")
    parser.add_argument("--mode", type=str, default="normal", help="Fault mode to inject: normal, latency_spike, error_burst, kill")
    args = parser.parse_args()

    print(f"Starting Load Generator in mode: {args.mode}")

    async with httpx.AsyncClient() as client:
        if args.mode != "normal":
            print(f"Injecting fault mode '{args.mode}' to target server...")
            try:
                await client.post(f"{TARGET_URL}/_fault?mode={args.mode}")
            except Exception as e:
                print(f"Failed to inject fault: {e}")
                
        print(f"Spawning {CONCURRENCY} concurrent workers...")
        tasks = [asyncio.create_task(worker(client)) for _ in range(CONCURRENCY)]
        
        # Run forever
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nLoad generator stopped.")

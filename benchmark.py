import asyncio
import time
from dotenv import load_dotenv

load_dotenv("Backend/.env")

from Backend.app.services.canvas_client import paginate_limited, _client, close_client
from Backend.app.core.database import count_courses, init_db, close_db

async def run_benchmark():
    await init_db()
    
    # Force client init
    c = _client()
    
    print("--- Starting Canvas Network Benchmark ---")
    
    start_time = time.time()
    # We fetch a page 10 times concurrently
    tasks = []
    for _ in range(10):
        tasks.append(paginate_limited("/courses", {"per_page": 10}, max_records=10))
    
    try:
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        print(f"Network calls: 10 parallel API requests completed in {elapsed:.3f} seconds.")
    except Exception as e:
        print(f"Canvas API test failed: {e}")

    print("\n--- Starting DB Concurrency Benchmark ---")
    start_time = time.time()
    
    db_tasks = []
    for _ in range(500):
        db_tasks.append(count_courses())
        
    await asyncio.gather(*db_tasks)
    elapsed = time.time() - start_time
    print(f"Database calls: 500 parallel SQLite reads completed in {elapsed:.3f} seconds.")

    await close_client()
    await close_db()

if __name__ == "__main__":
    asyncio.run(run_benchmark())

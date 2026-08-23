import asyncio
import os
import signal
import sys
from streaming_pipeline import HighThroughputClimateStreamEngine

async def main():
    print("=" * 80)
    print(" AquaCrop AI Asynchronous Streaming & Batch Worker Started")
    print("=" * 80)
    
    batch_size = int(os.getenv("STREAM_BATCH_SIZE", "500"))
    stream_engine = HighThroughputClimateStreamEngine(batch_size=batch_size)

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def handle_shutdown(sig):
        print(f"\n[Worker] Received shutdown signal ({sig.name}). Flushing batches and exiting gracefully...")
        stream_engine.is_running = False
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s=sig: handle_shutdown(s))
        except NotImplementedError:
            # Fallback for Windows event loops
            pass

    # Start consumer worker loop
    print(f"[Worker] Actively listening for climate telemetry streams (Batch Size: {batch_size})...")
    consumer_task = asyncio.create_task(stream_engine.start_consumer_worker())

    await consumer_task
    print("[Worker] Shutdown completed cleanly.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Worker] KeyboardInterrupt received. Exiting.")
        sys.exit(0)

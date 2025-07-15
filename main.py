import asyncio

from config.settings import ZEEBE_ADDRESS
from pyzeebe import create_insecure_channel, ZeebeClient, ZeebeWorker
from tasks.worker_tasks import CamundaWorkerTasks
from utils.logging_utils import setup_logging


async def main():
    logger = setup_logging()
    logger.info("Starting Camunda Service")

    logger.info(f"Connecting to Zeebe at {ZEEBE_ADDRESS}")
    channel = create_insecure_channel(grpc_address=ZEEBE_ADDRESS)
    client = ZeebeClient(channel)
    worker = ZeebeWorker(channel)

    logger.info("Registering worker tasks")
    CamundaWorkerTasks(worker, client)
    logger.info("Starting Zeebe worker")
    try:
        await worker.work()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
    except Exception as e:
        logger.error(f"Error in worker: {e}", exc_info=True)
    finally:
        logger.info("Closing Zeebe connections")
        await channel.close()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import json
import time

import asyncclick as click
from aiokafka import AIOKafkaProducer
from kafka.errors import KafkaConnectionError
from loguru import logger

from ozon import Catalog


def dump_to_bytes(obj):
    return json.dumps(obj).encode("utf-8")


@click.command()
@click.option("--category", required=True)
@click.option("--pages", default=5)
@click.option("--sorting", default="new")
async def main(category: str, pages: int, sorting: str) -> None:
    time.sleep(10)
    producer = AIOKafkaProducer(
        bootstrap_servers="kafka:9092", value_serializer=dump_to_bytes
    )
    await producer.start()

    async with Catalog() as catalog:
        for page in range(1, pages + 2):
            response = await catalog.get_raw(category, page=page, sorting=sorting)
            data = await response.json()
            msg = {
                "url": str(response.url),
                "category": category,
                "page": page,
                "sorting": sorting,
                "data": data,
                "status": response.status,
                "headers": dict(response.headers),
            }
            logger.debug(f"Sending {response.url} raw data")
            await producer.send_and_wait("ozon_category", msg)
    await producer.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

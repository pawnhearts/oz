import asyncio
import json
import time

import aiokafka
from loguru import logger

from ozon import Catalog


def dump_to_bytes(obj):
    return json.dumps(obj).encode("utf-8")


async def main() -> None:
    time.sleep(10)
    consumer = aiokafka.AIOKafkaConsumer(
        "ozon_category",
        loop=loop, bootstrap_servers='kafka:9092'
    )
    producer = aiokafka.AIOKafkaProducer(
        bootstrap_servers="kafka:9092", value_serializer=dump_to_bytes
    )
    await consumer.start()
    await producer.start()

    try:
        async for msg in consumer:
            logger.debug(
                "{}:{:d}:{:d}: key={} value={} timestamp_ms={}".format(
                    msg.topic, msg.partition, msg.offset, msg.key, msg.value,
                    msg.timestamp)
            )
            catalog_page = json.loads(msg.value.decode('utf-8'))
            if catalog_page['status'] != 200:
                logger.warning(f'Non-200 status code on {catalog_page["url"]}')
            else:
                items = Catalog.get_items(catalog_page['data'])
                if items is None:
                    logger.warning(f'Cannot find items on {catalog_page["url"]}')
                else:
                    for item in items:
                        product = Catalog.item_to_product(item)
                        product['timestamp'] = msg.timestamp
                        logger.debug(product)
                        await producer.send_and_wait('ozon_products', product)

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

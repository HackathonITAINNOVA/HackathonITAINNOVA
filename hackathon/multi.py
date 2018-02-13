from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing.dummy import Semaphore

from . import config
import logging
logger = logging.getLogger(__name__)


def paralelize(consumer, producer):
    """ Implements a queued production of items to paralelize, limits RAM usage.

    Args:
        consumer (function): Ingest and process items
        producer (generator): Yields items to be consumed
    """
    logger.info("Starting paralelization")
    pool = ThreadPool(config.settings.NUM_CONCURRENT_WORKERS)
    semaphore = Semaphore(config.settings.QUEUE_SIZE)

    def producer_queued():
        for item in producer:
            semaphore.acquire()
            yield item

    def consumer_queued(item):
        semaphore.release()
        return consumer(item)

    # imap uses correctly the generator, is more memory efficient
    pool.imap_unordered(consumer_queued, producer_queued())
    logger.info("Finishing paralelization")
    pool.close()
    pool.join()

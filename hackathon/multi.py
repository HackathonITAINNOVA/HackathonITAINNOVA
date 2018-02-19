from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing.dummy import Semaphore

from . import config
import logging
logger = logging.getLogger(__name__)


class Pool(object):

    def __init__(self):
        self.semaphore = Semaphore(config.settings.QUEUE_SIZE)

    def queue_producer(self, producer):
        """Yields items as soon as the semaphore allows."""
        try:
            for item in producer:
                self.semaphore.acquire()
                yield item
        except:
            logger.exception("Error in producer parallel task")

    def queue_consumer(self, consumer):
        """Returns item consumption function that signals the semaphore."""

        def consumer_function(item):
            self.semaphore.release()
            try:
                consumer(item)
            except:
                logger.exception("Error in consumer parallel task")

        return consumer_function

    def parallelize(self, consumer, producer):
        """Implements a queued production of items to paralelize, limits RAM usage.
        imap() uses correctly the generator, is more memory efficient
        imap_unordered() does not wait on each item to be processed

        Args:
            consumer (function): Ingest and process items
            producer (generator): Yields items to be consumed
        """
        logger.info("Starting paralelization")

        self.pool = ThreadPool(config.settings.NUM_CONCURRENT_WORKERS)

        self.pool.imap_unordered(self.queue_consumer(consumer), self.queue_producer(producer))

        self.pool.close()
        self.pool.join()

        logger.info("Finishing paralelization")

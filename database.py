import redis
import os

r = redis.Redis(
    host = 'redis-13002.c282.east-us-mz.azure.cloud.redislabs.com',
    port = 13002,
    password = os.getenv('DB_PASSWORD'),
    decode_responses = True
)
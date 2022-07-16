import redis

r = redis.Redis(
    host = 'redis-13002.c282.east-us-mz.azure.cloud.redislabs.com',
    port = 13002,
    password = 'hURchKfPvsLovNfIU6JLRmV80Iu1v9cP',
    decode_responses = True
)
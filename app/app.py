import os
import random
import string
import logging

import asyncio

from sanic import Sanic, response
from sanic_jinja2 import SanicJinja2

import asyncpg

db_user = os.getenv('POSTGRES_USER')
db_pass = os.getenv('POSTGRES_PASSWORD')
db_host = os.getenv('POSTGRES_HOST', 'localhost')
db_port = os.getenv('POSTGRES_PORT', 5432)
db_name = os.getenv('POSTGRES_DB', 'redirects')

DSN = 'postgres://{0}:{1}@{2}:{3}/{4}'.format(db_user, db_pass, db_host, db_port, db_name,)
LATEST_LINKS = 5
VERSION = '0.0.2'

app = Sanic(__name__)

app.static('/static', './static')
jinja = SanicJinja2(app)

log = logging.getLogger('url')


async def generate_url(length=6) -> str:
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


async def connect_db(dsn: str, retries=5):
    while retries:
        try:
            pool = await asyncpg.create_pool(dsn=dsn)
            return pool
        except Exception as e:
            log.error('Unable to connect db. Message: %s. Retries = %d' % (e, retries))
            await asyncio.sleep(3)
            await connect_db(dsn=dsn, retries=retries - 1)
    log.error('Unable to connect db. Stop.')
    raise ConnectionRefusedError


@app.listener('before_server_start')
async def init_db(app, loop):
    app.pool = await connect_db(dsn=DSN)


@app.route('/', methods=['GET', 'POST'])
async def index(request):
    try:
        pool = app.pool
        async with pool.acquire() as conn:
            async with conn.transaction():
                if request.method == 'POST':
                    original_url = request.form.get('url')
                    short_url = await conn.fetchval('SELECT short_url FROM redirects WHERE original_url = $1;', original_url)
                    if not short_url:
                        short_url = await generate_url()
                        await conn.execute('INSERT INTO redirects (short_url, original_url) VALUES ($1, $2);', short_url, original_url)
                    return response.redirect(app.url_for('result', short_url=short_url))
                latest_links = await conn.fetch('SELECT * FROM redirects ORDER BY created_at DESC LIMIT $1;', LATEST_LINKS)
                return jinja.render('index.html', request, links=latest_links)
    except (asyncio.TimeoutError, ConnectionRefusedError):
        await connect_db(dsn=DSN)


@app.route('/url/<short_url>')
async def result(request, short_url):
    return jinja.render('result.html', request, url=short_url)


@app.route('/<url>', methods=['GET'])
async def redirect(request, url):
    try:
        pool = app.pool
        async with pool.acquire() as conn:
            async with conn.transaction():
                original_url = await conn.fetchval('SELECT original_url FROM redirects WHERE short_url = $1;', url)
                if not original_url:
                    return response.json({'original_url': 'not found'})
        if 'http' not in original_url:
            original_url = 'http://' + original_url

        return response.redirect(original_url)
    except (asyncio.TimeoutError, ConnectionRefusedError):
        await connect_db(dsn=DSN)


@app.route('/health')
async def healthcheck(request):
    try:
        async with app.pool.acquire() as conn:
            async with conn.transaction():
                resp = await conn.fetchval('SELECT 1;')
                if resp:
                    return response.json({'db_access_ok': True,
                                          'version': VERSION})
                else:
                    raise
    except Exception as e:
        return response.json({'db_access_ok': False,
                              'info': str(e),
                              'version': VERSION})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=os.getenv('DEBUG'))

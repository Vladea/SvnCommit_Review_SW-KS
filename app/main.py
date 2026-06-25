import logging

from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import APP_HOST, APP_PORT
from app.database import init_db
from app.logging_config import setup_logging
from app.routes import api_router
from app.scheduler import scheduler, reload_schedule

logger = setup_logging()

app = FastAPI(title='SVN AI Review V2.0', version='2.0.0')
app.mount('/static', StaticFiles(directory='app/static'), name='static')
app.include_router(api_router)


@app.get('/')
def index(response: Response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return FileResponse('app/static/index.html', headers={
        'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'
    })


@app.get('/api/health')
def health():
    return {'status': 'ok', 'version': '2.0.0'}


@app.on_event('startup')
def startup():
    init_db()
    if not scheduler.running:
        scheduler.start()
        logger.info('Scheduler started')
    reload_schedule()
    logger.info(f'SVN AI Review V2.0 started on {APP_HOST}:{APP_PORT}')


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host=APP_HOST, port=APP_PORT, reload=False)

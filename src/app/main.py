from fastapi import APIRouter, FastAPI

from src.app.routers import projects, rooms, users

app = FastAPI(
    title='Group Sessions Platform API',
    version='1.0.0',
)

api_router = APIRouter(prefix='/api/v1')

api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(rooms.router)

app.include_router(api_router)


@app.get('/health')
async def healthcheck():
    return {'status': 'ok'}

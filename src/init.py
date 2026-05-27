import asyncio

from src.app.init import init_rbac

if __name__ == '__main__':
    asyncio.run(init_rbac())

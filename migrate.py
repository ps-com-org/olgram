import asyncio
from olgram.migrations.custom import migrate


if __name__ == '__main__':
    asyncio.run(migrate())

"""Support Peewee ORM with asyncio."""


__version__ = "0.12.4"


from .model import AIOModel as Model
from .manager import Manager

__all__ = 'Manager', 'Model'

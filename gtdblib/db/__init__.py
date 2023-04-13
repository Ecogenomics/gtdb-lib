from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gtdblib.config import CONFIG


class GenericEngine:

    def __init__(self, db_name: str):
        self.db_name: str = db_name
        self._engine = None
        self._session = None

    @property
    def url(self):
        return f'postgresql://{CONFIG.db_user}:{CONFIG.db_pass}@{CONFIG.db_host}/{self.db_name}'

    def __enter__(self):
        if self._engine is None:
            self._engine = create_engine(
                self.url,
                pool_size=5,
                max_overflow=20,
                pool_recycle=3600
            )
        if self._session is None:
            session = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
            self._session = session()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()

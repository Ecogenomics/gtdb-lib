from urllib.parse import quote

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
        # the user and password are escaped as they may contain characters
        # with special meaning in a URL (e.g. '@', ':', '/')
        user = quote(str(CONFIG.db_user), safe='')
        password = quote(str(CONFIG.db_pass), safe='')
        return f'postgresql://{user}:{password}@{CONFIG.db_host}/{self.db_name}'

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

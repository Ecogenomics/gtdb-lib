
from gtdblib.db.common import DB_COMMON, LpsnHtml

from sqlalchemy import select
def main():
    with DB_COMMON as db:

        stmt = select(LpsnHtml).where(LpsnHtml.id == 1)
        res = db.execute(stmt).fetchall()

        print(res)



if __name__ == '__main__':
    main()
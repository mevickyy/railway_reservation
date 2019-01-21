from django.db import connections, OperationalError, ProgrammingError
from django import db
import time
import logging

logger = logging.getLogger("sql")


class DBquery:

    def __init__(self, sql, *args, **kwargs):
        self.verbose = kwargs.get("v", 0)
        self.connection = kwargs.get("connection", "default")
        retries = kwargs.get("retry", 3)
        retry = retries
        while retry > -1:
            try:
                self.cursor = connections[self.connection].cursor()
                _sql = sql % args
                if self.verbose:
                    print(_sql, flush=True)
                    logger.info(_sql)
                self.cursor.execute(sql, args)
                retry = -1
            except OperationalError as ex:
                if(ex.args[0] == 2006):  # MySQL server has gone away
                    if retry == 0:
                        raise ex
                    self.cursor.close()
                    self.close_dbs()
                    retry -= 1
                    time.sleep(1)
                    print("try: %s" % (retries - retry))
                else:
                    raise ex
            except ProgrammingError as ex:
                if(ex.args[0] == 1064):  # SQL Syntax error
                    _sql = sql % args
                    print(_sql)
                    logger.exception(ex,
                                     extra={"query":
                                            {"sql": _sql,
                                             "args": args}
                                            })

                raise ex

    def close_dbs(self):
        db.connections.close_all()

    @property
    def lastrowid(self):
        lid = self.cursor.lastrowid
        self.cursor.close()
        return lid

    def as_dicts(self):
        columns = [col[0] for col in self.cursor.description]
        listofdicts = [
            dict(zip(columns, row))
            for row in self.cursor.fetchall()
        ]
        self.cursor.close()
        return listofdicts

    def as_dict(self):
        dikt = {}
        if self.cursor.rowcount:
            row = self.cursor.fetchone()
            columns = [col[0] for col in self.cursor.description]
            dikt = dict(zip(columns, row))
        self.cursor.close()
        return dikt

    def as_list(self):
        List = [row[0] for row in self.cursor.fetchall()]
        self.cursor.close()
        return List

    def as_value(self, default=None):
        value = None
        if self.cursor.rowcount:
            value = self.cursor.fetchone()[0]
        self.cursor.close()
        return value if value is not None else default

    def as_map(self, column_name):
        column_names = [col[0] for col in self.cursor.description]
        column_postion = column_names.index(column_name)
        dikt = {row[column_postion]: dict(zip(column_names, row)) for row in self.cursor.fetchall()}
        self.cursor.close()
        return dikt

    def as_group(self, column_name):
        column_names = [col[0] for col in self.cursor.description]
        column_postion = column_names.index(column_name)
        groups = {}
        for row in self.cursor.fetchall():
            try:
                groups[row[column_postion]].append(dict(zip(column_names, row)))
            except KeyError:
                groups[row[column_postion]] = [dict(zip(column_names, row))]
        self.cursor.close()
        return groups

    def exists(self):
        count = self.cursor.rowcount
        self.cursor.close()
        return count

    # eg. DBquery("SELECT * FROM comments_updates.comments where id = %s", 54503).as_dicts()
    # eg. DBquery("SELECT * FROM comments_updates.comments where id = %s and id=%s", 54503, 1234).as_dicts()


def lazzydbfetch(count_sql,
                 sql,
                 sql_arguments_kwargs=[],
                 limit=100,
                 v=0,
                 structure="as_dicts",
                 return_count=False):
    """
    :param sql: query should not contain limit, offset keyword
    :param sql_arguments_kwargs: arguments for dbfetch
    :param limit:
    :return: list of dictionaries generator
    """
    sql = sql.strip()
    count_sql = count_sql.strip()

    # find total no of rows
    total_rows = DBquery(count_sql).as_value()

    sql_limit_offset_template = " LIMIT {} OFFSET {}".format
    for sql_offset in range(0, total_rows, limit):
        _sql = sql + sql_limit_offset_template(limit, sql_offset)
        fetched_rows = getattr(DBquery(_sql, *sql_arguments_kwargs, v=v), structure)()
        for _row in fetched_rows:
            yield _row


def generate_sqlin(values):
    in_string = ""
    for value in values:
        in_string += str(value)+","
    return in_string.rstrip(",")

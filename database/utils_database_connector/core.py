import os

import pandas as pd
from database.utils_configs.databases import DatabaseConfig, settings
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlglot import parse_one
from sqlglot.errors import ParseError


class Database:
    def __init__(self, database: str, max_execution_time: int = 180):
        """
        Initialize the database connector. There are two types of databases supported: PostgreSQL, MySQL.
        The configuration of the database will be obtained from the utils_configs component.

        Args:
            database: the database name
            max_execution_time: the maximum execution time for a query in seconds. Default is 180s.
        """
        self.config = self._get_database_from_name(database)
        self.max_execution_time = max_execution_time

        if "TEST" in os.environ:
            hostname = self.config.test_hostname
        elif "DEV" in os.environ:
            hostname = "localhost"
        else:  # pragma: no cover
            hostname = self.config.hostname

        self.connection_uri = (
            f"{self.config.type}+{self.config.driver}://{self.config.username}:"
            f"{self.config.password}@{hostname}:{self.config.port}/{self.config.name}"
        )

        if self.config.type == "postgresql":
            timeout_arg = {
                "options": f"-c statement_timeout={max_execution_time * 1000}"
            }
        elif self.config.type == "mysql":
            timeout_arg = {"read_timeout": max_execution_time}
        else:
            raise ValueError("Invalid database type")

        self.engine = create_engine(self.connection_uri, connect_args=timeout_arg)

        self.schemas = ",".join(["'" + k + "'" for k in self.config.schemas])

    @staticmethod
    def _get_database_from_name(name) -> DatabaseConfig:
        for db in settings.databases:
            if name in db.aliases:
                return db
        raise Exception("Invalid database name")  # pragma: no cover

    def _parse_query(self, query: str, limit: int, order_by_rand=False):
        pars = parse_one(query)

        if order_by_rand:
            if self.config.type != "mysql":
                pars = pars.order_by("random()")
            else:
                pars = pars.order_by("rand()")

        if limit not in (-1, 0):
            pars = pars.limit(limit)

        sql = pars.sql(dialect="mysql" if self.config.type == "mysql" else "postgres")
        # print(sql)
        return sql

    def execute(
        self,
        sql: str,
        limit: int = 500,
        order_by_rand: bool = False,
        fix_dates: bool = False,
        dates_format: str = "%d/%m/%Y",
    ) -> pd.DataFrame | dict:
        """
        Execute a given SQL query

        Args:
            sql: the sql query
            limit: the maximum number of rows to return
            order_by_rand: whether to order the results randomly
            fix_dates: whether to fix the dates format
            dates_format: the dates format

        Returns:
            results: the results of the query or a dictionary with an error message
        """

        try:
            query = self._parse_query(sql, limit, order_by_rand)

            with self.engine.begin() as conn:
                df = pd.read_sql(text(query), con=conn)
            conn.close()
            self.engine.dispose()

            if fix_dates:
                mask = df.astype(str).apply(
                    lambda x: x.str.match(r"(\d{2,4}-\d{2}-\d{2,4})+").all()
                )
                df.loc[:, mask] = (  # type: ignore
                    df.loc[:, mask]  # type: ignore
                    .apply(pd.to_datetime)
                    .apply(lambda x: x.dt.strftime(dates_format))
                )
        except SQLAlchemyError as e:
            logger.error(f"sqlalchemy error {str(e.__dict__['orig'])}")
            return {"error": str(e.__dict__["orig"])}
        except ParseError as e:
            if len(e.errors) > 0:
                logger.error(f"parse error {e.errors[0]['description']}")
                return {"error": e.errors[0]["description"]}
            logger.error(f"parse error {str(e)}")
            return {"error": str(e)}
        except RuntimeError as e:
            logger.error(f"runtime error {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"other exception {e} {sql}")
            return {"error": "Something went wrong with your query."}
        return df

    def executemany(self, sql: str, data: list):
        """
        Execute many SQL queries in a batch (for bulk INSERT, UPDATE, or DELETE operations)

        Args:
            sql: the SQL query template
            data: list of dictionaries containing the data to be used in the query
        """
        try:
            with self.engine.begin() as conn:
                conn.execute(text(sql), data)
            return {"status": "success"}
        except SQLAlchemyError as e:
            return {"error": str(e.__dict__["orig"])}
        except Exception as e:
            print("other exception", e)
            return {"error": "Something went wrong with your query."}

        # TODO: Parse the query for the specific database type (PostgreSQL or MySQL)

    def get_tables_and_columns(self, blacklist_tables: list = []) -> dict:
        """
        Return the schema of the database

        Args:
            blacklist_tables: the tables to exclude from the results


        Examples:
            ```
            {
                'tables': ['table1', 'table2'],
                'columns': ['table1.column1', 'table1.column2', 'table2.column1'],
                'table': {
                    'table1': [0, 1],
                    'table2': [2]
                }
            }
            ```
        """
        q = f"""
            SELECT table_name,column_name
            FROM information_schema.COLUMNS
            WHERE table_schema in ({self.schemas})
        """
        if (
            len(blacklist_tables) == 0 and len(self.config.blacklist_tables) > 0
        ):  # blacklist not provided, use default
            blacklist_tables = self.config.blacklist_tables

        if len(blacklist_tables) > 0:
            blacklist = " AND ".join(
                ["table_name not like '" + k + "'" for k in blacklist_tables]
            )
            q += " AND " + blacklist

        results = self.execute(q, limit=0)
        return self._parse_tables_and_columns(results)

    @staticmethod
    def _parse_tables_and_columns(results) -> dict:
        column_id = 0
        parsed = {"tables": [], "columns": [], "table": {}}

        for _, row in results.iterrows():
            table, column = row

            if table not in parsed["tables"]:
                parsed["tables"].append(table)
                parsed["table"][table] = []

            parsed["columns"].append(table + "." + column)
            parsed["table"][table].append(column_id)

            column_id += 1

        return parsed

    def get_joins(self) -> dict:
        """
        Return the joins for the database

        Examples:
            ```
            {
                'table1': {
                    'table2': 'table1.column1=table2.column1',
                    'table3': 'table1.column2=table3.column2'
                },
            }
            ```
        """
        if self.config.type != "mysql":
            query = f"""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM
                information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' and tc.table_schema in ({self.schemas})
            """
        else:
            query = f"""
            SELECT
                TABLE_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM
                INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE REFERENCED_COLUMN_NAME is not null
            AND CONSTRAINT_SCHEMA in ({self.schemas})
            """
        results = self.execute(query, limit=0)
        return self._parse_joins(results)

    @staticmethod
    def _parse_joins(results) -> dict:
        joins = {}
        for _, join in results.iterrows():
            for i in [0, 2]:
                thisTable = join[i]
                otherTable = join[0] if i == 2 else join[2]

                if thisTable not in joins:
                    joins[thisTable] = {}

                if otherTable not in joins[thisTable]:
                    joins[thisTable][otherTable] = []

                condition = join[0] + "." + join[1] + "=" + join[2] + "." + join[3]
                joins[thisTable][otherTable].append(condition)

        for tableA, valA in joins.items():
            for tableB, valB in valA.items():
                joins[tableA][tableB] = " AND ".join(valB)

        return joins


if __name__ == "__main__":
    # q = """
    # SELECT
    #         a.fullname, a.orcid,
    #         COUNT(r.id) AS publication_num,
    #         STRING_AGG(r.id, '; ') AS publication_ids
    #     FROM author a
    #     LEFT JOIN result_author ra ON a.id = ra.author_id
    #     LEFT JOIN result r ON ra.result_id = r.id
    #     WHERE a.id = '00011ab1bc9af9fbfbabd4d8cca6fa76'
    #     GROUP BY a.id, a.fullname, a.orcid;
    # """
    # print(Database("fc4eosc").execute(q, limit=10))
    db = Database("cordis", max_execution_time=0.0001)
    print(db.execute("SELECT COUNT(*) FROM projects"))

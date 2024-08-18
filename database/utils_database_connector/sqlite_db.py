from collections import defaultdict

import pandas as pd
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


class DatabaseSqlite:
    def __init__(self, database: str):
        """.
        Initialize the database connector for SQLite by providing the path to the database file.
        Note: SQLite does not have all the functionalities provided by the Database connector.

        Args:
            database: the database path i.e. "path/to/database.db"
        """
        self.connection_uri = f"sqlite:///{database}"
        self.engine = create_engine(self.connection_uri)

    def execute(self, sql: str) -> pd.DataFrame | dict:
        """
        Execute a given SQL query

        Args:
            sql: the sql query

        Returns:
            results: the results of the query or a dictionary with an error message
        """
        try:
            with self.engine.begin() as conn:
                df = pd.read_sql(text(sql), con=conn)
            conn.close()
            self.engine.dispose()
        except SQLAlchemyError as e:
            logger.error(f"sqlalchemy error {str(e.__dict__['orig'])}")
            return {"error": str(e.__dict__["orig"])}
        except Exception as e:
            logger.error(f"General error: {e} for query {sql}")
            return {"error": "Something went wrong with your query."}
        return df

    def get_tables_and_columns(self):
        tables_cols_df = self.execute(
            """
            SELECT m.name as tableName,
                   p.name as columnName
            FROM sqlite_master m
            left outer join pragma_table_info((m.name)) p
                 on m.name <> p.name
            order by tableName, columnName
            ;
        """
        )

        res = defaultdict(list)
        for _, row in tables_cols_df.iterrows():
            res[row["tableName"]].append(row["columnName"])
        return res


if __name__ == "__main__":
    db = DatabaseSqlite("Car_Database.db")
    print(db.get_tables_and_columns())

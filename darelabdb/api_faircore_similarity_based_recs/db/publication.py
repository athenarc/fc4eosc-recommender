from datetime import date
from typing import Optional, Tuple

from darelabdb.utils_database_connector.core import Database


def get_publication_preview(
    result_id: str, query_executor: Database
) -> Tuple[str, str, Optional[date], str, str]:
    res = query_executor.execute(
        f"SELECT result.title, result.type, result.publication_date, result.publisher, result.authors "
        f"FROM result "
        f"WHERE result.id='{result_id}'"
    )

    return (
        res.title[0],
        res.type[0],
        res.publication_date[0],
        res.publisher[0],
        res.authors[0],
    )

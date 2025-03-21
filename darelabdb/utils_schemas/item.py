from typing import Any, Dict, List, Set, Union

import pydantic

DEFAULT_ATTRIBUTE_TYPES = {
    "metadata_attributes": lambda: [],
    "text_attributes": lambda: "",
}

item_id_type = Union[int, str]
metadata_attribute_type = List[Union[str, int, float]]


class Item(pydantic.BaseModel):
    """
    The **Item model** represents an item in your catalog. This can be a service/product/movie/... or anything
    that fits the use case of your recommender system.

    **Example**
    ```python
    item = Item(
                item_id=1,
                metadata_attributes={"genre": ["action", "drama"]},
                text_attributes={"title": "The Matrix", "description": "A movie about a matrix"},
            )
    ```

    **Arguments**

    * `item_id (Union[int, str])`: The unique identifier of the item.
    * `metadata_attributes (Dict[str, List[Any]])`: A dictionary of metadata attributes. The key is the attribute type.
    * `text_attributes (Dict[str, str])`: A dictionary of text attributes. The key is the attribute type.
    """

    item_id: item_id_type
    metadata_attributes: Dict[str, metadata_attribute_type] = {}
    text_attributes: Dict[str, str] = {}

    model_config = pydantic.ConfigDict(
        extra="forbid"
    )  # allow only fields defined in the model


def get_superset_schema_of_items(items: List[Item]) -> Dict[str, Set[str]]:
    """
    This function returns the superset schema of a list of items.

    Args:
        items (List[Item]): List of all the items (i.e. list of the whole catalog)

    Returns:
        A dictionary with the superset schema of the items

    """
    current_schema = {
        "metadata_attributes": set(),
        "text_attributes": set(),
    }

    for item in items:
        for attribute_type in current_schema.keys():
            for attribute in item.__getattribute__(attribute_type):
                if attribute not in current_schema[attribute_type]:
                    current_schema[attribute_type].add(attribute)

    return current_schema


def complete_item_based_on_schema(item: Item, schema: Dict[str, Set[str]]) -> Item:
    """
    This function completes an item based on a given schema.
    It adds empty lists for all the attributes that are not present
    Args:
        item (Item): The Item to complete
        schema (Dict[str, Set[str]]): The schema to use to complete the item

    Returns:
        The completed item
    """
    for attribute_type in schema.keys():
        for attribute in schema[attribute_type]:
            if attribute not in item.__getattribute__(attribute_type):
                item.__getattribute__(attribute_type)[attribute] = (
                    DEFAULT_ATTRIBUTE_TYPES[attribute_type]()
                )

    return item


def get_metadata_values_of_attribute(items: List[Item], attribute: str) -> Set[Any]:
    """
    This function returns all the values of a given attribute for a list of items.

    Args:
        items (List[Item]): List of items
        attribute (str): The attribute to get the values from

    Returns:
        A set of all the values of the given attribute
    """
    values = set()

    for item in items:
        if attribute in item.metadata_attributes:
            for value in item.metadata_attributes[attribute]:
                values.add(value)

    return values

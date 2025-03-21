from typing import Any, Dict, List, Union

import pydantic
from pydantic import model_serializer


class UserState(pydantic.BaseModel):
    """
    The **UserState model** aims in representing what the user is currently doing.
    Currently, it includes the item that the user is viewing and the history of items that the user has *interacted*
    in the past.

    An interaction is defined by the use case (i.e. viewing, buying, rating, etc.).

    !!! warning

        Currently a field validator is used to check that the item history
        **does not contain duplicate items**.

    **Example**
    ```python
    user_state = UserState(
                viewed_item_id=1,
                item_history=[2, 3, 4]
            )
    ```

    **Arguments**

    * `item_id (Union[int, str])`: The unique identifier of the item.
    * `score (float)`: The score of the recommendation.
    """

    viewed_item_id: Union[int, str]
    item_history: List[Union[int, str]] = []

    model_config = pydantic.ConfigDict(
        extra="forbid"
    )  # allow only fields defined in the model

    @pydantic.field_validator("item_history")
    @classmethod
    def check_no_duplicate_items(cls, item_history: List[Union[int, str]]):
        item_ids = set()
        duplicate_items = set()
        for item_id in item_history:
            if item_id in item_ids:
                duplicate_items.add(item_id)
            item_ids.add(item_id)

        assert (
            len(duplicate_items) == 0
        ), f"Item history contains duplicate items: {duplicate_items}"

        return item_history

    @model_serializer
    def serialize_user_state(self) -> Dict[str, Any]:
        return {
            "viewed_item_id": str(self.viewed_item_id),
            "item_history": [str(item_id) for item_id in self.item_history],
        }

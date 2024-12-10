from collections.abc import Sequence
from datetime import date
from typing import Annotated
from uuid import UUID

import httpx
import polars as pl
import polars.selectors as cs
from fastapi import APIRouter, Depends, HTTPException, status
from httpx import HTTPStatusError
from pydantic import BaseModel

from ...core.db import User
from ...core.users import get_current_user
from ...dependencies import get_http_client
from ...models import BudgetDetailResponse, ErrorResponse


class Transaction(BaseModel):
    id: UUID
    date: date
    amount: int

    account_id: UUID
    account: str

    payee_id: UUID
    payee: str

    category_id: UUID
    category: str

    category_group_id: UUID
    category_group: str


def construct_df(models: Sequence[BaseModel] | None):
    return pl.LazyFrame(
        [model.model_dump(mode="json") for model in models] if models else None,
        infer_schema_length=None,
    )


router = APIRouter()


@router.get(
    "/",
    response_model=list[Transaction],
    responses={
        status_code: {"model": ErrorResponse}
        for status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ]
    },
)
async def read_transactions(
    user: Annotated[User, Depends(get_current_user)],
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
):
    try:
        response = (
            await client.get(
                "/budgets/last-used",
                headers={
                    "Authorization": f"Bearer {user.oauth_accounts[0].access_token}"
                },
            )
        ).raise_for_status()
    except HTTPStatusError as e:
        error = ErrorResponse.model_validate_json(e.response.text).error

        raise HTTPException(e.response.status_code, detail=error.model_dump())

    budget = BudgetDetailResponse.model_validate_json(response.text).data.budget

    subtransactions = construct_df(budget.subtransactions).select(
        "amount", "payee_id", "category_id", id="transaction_id"
    )
    transactions = (
        construct_df(budget.transactions)
        .select("id", "date", "amount", "account_id", "payee_id", "category_id")
        .update(subtransactions, how="left", on="id")
    )

    accounts = construct_df(budget.accounts).select(account_id="id", account="name")

    payees = construct_df(budget.payees).select(payee_id="id", payee="name")

    category_groups = construct_df(budget.category_groups).select(
        category_group_id="id", category_group="name"
    )
    categories = (
        construct_df(budget.categories)
        .select("category_group_id", category_id="id", category="name")
        .join(category_groups, on="category_group_id")
    )

    return (
        transactions.join(accounts, how="left", on="account_id")
        .join(payees, how="left", on="payee_id")
        .join(categories, how="left", on="category_id")
        # Handle invalid UUIDs
        .with_columns(cs.ends_with("id").str.split("_").list.first())
        .filter(
            # Exclude transfer transactions
            pl.col("category").is_not_null(),
            # Exclude inflow transactions
            pl.concat_list("category_group", "category")
            != ["Internal Master Category", "Inflow: Ready to Assign"],
        )
        .collect()
        .to_dicts()
    )

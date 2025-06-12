from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field


class CommonQueryParams(BaseModel):
    id: UUID | str | None = Field(alias="_id", validation_alias=AliasChoices("id", "_id"), default=None)
    updated_at: str | None = Field(
        alias="_lastUpdated",
        default=None,
        validation_alias=AliasChoices("updated_at", "_lastUpdated"),
    )

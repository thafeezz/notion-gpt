from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv
from pydantic import BaseModel
import httpx, os, json

app = FastAPI()

load_dotenv()

INPUT_JSON = [
    {
        "name": "Reverse Linked List",
        "tags": ["Linked List"],
        "summary": "iterate thru list, set pointers the opposite direction",
        "complexity": "O(n) time, O(1) space",
    },
]

headers = {
    "Authorization": f"Bearer {os.getenv('INTEGRATION_TOKEN')}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


class RequestBody(BaseModel):
    page_id: str
    title: str
    properties: dict


@app.get("/pages/")
async def get_pages(query: str = Query(None)):
    if query:
        url = "https://api.notion.com/v1/search"

        data = {"query": query, "filter": {"property": "object", "value": "page"}}

        page_response = []
        database_response = []

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=data)
                pages = response.json()

                if pages["results"]:
                    for page in pages["results"]:
                        if page["parent"]["type"] == "workspace":
                            page_response.append(
                                {
                                    "title": page["properties"]["title"]["title"][0][
                                        "plain_text"
                                    ],
                                    "id": page["id"],
                                }
                            )
                        else:
                            database_response.append(
                                {
                                    "title": page["properties"]["Name"]["title"][0][
                                        "plain_text"
                                    ],
                                    "pageid": page["id"],
                                    "databaseid": page["parent"]["database_id"],
                                }
                            )

                    return {
                        "pages": page_response,
                        "databases": database_response,
                    }
                else:
                    raise HTTPException(status_code=404, detail="Page not found")

            except httpx.HTTPStatusError as exc:
                print(f"HTTP status error: {exc}")
    else:
        raise HTTPException(status_code=400, detail="Query cannot be empty")


@app.post("/create_database/")
async def create_database(request: RequestBody):
    url = "https://api.notion.com/v1/databases/"

    data = {
        # required field
        "parent": {
            "type": "page_id",
            "page_id": request.page_id,
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": request.title,
                },
            }
        ],
        # required field
        "properties": request.properties,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=data)
            return response.json()
        except httpx.HTTPStatusError as exc:
            print(f"HTTP status error: {exc}")


@app.get("/get_databases")
async def get_databases():
    url = "https://api.notion.com/v1/search"

    data = {"filter": {"property": "object", "value": "database"}}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=data)
            databases = response.json()

            return {
                database["title"][0]["plain_text"]: database["id"]
                for database in databases["results"]
            }

        except httpx.HTTPStatusError as exc:
            print(f"HTTP status error: {exc}")


@app.post("/create")
async def create_item():
    url = "https://api.notion.com/v1/databases/"

    

import uvicorn
from fastapi import FastAPI
from mangum import Mangum
from pydantic import BaseModel
from rag_app.query_rag import QueryResponse, query_rag
from query_model import QueryModel

app = FastAPI()
handler = Mangum(app)  # entry point for AWS Lambda

class SubmitQueryRequest(BaseModel):
    query_text: str

@app.get("/")
def index():
    return {"Hello": "World"}

@app.get("/get_query")
def get_query_endpoint(query_id: str) -> QueryModel:
    query = QueryModel.get_item(query_id)
    return query

@app.post("/submit_query")
def submit_query_endpoint(request: SubmitQueryRequest) -> QueryModel:

    query_response = query_rag(request.query_text)
    
    # create the query item and put it into the db
    new_query = QueryModel(
        query_text=request.query_text,
        answer_text=query_response.response_text,
        sources=query_response.sources,
        is_complete=True,
    )
    new_query.put_item()
    
    return new_query

if __name__ == "__main__":
    port = 8000
    print(f"Running the FastAPI server on port {port}.")
    uvicorn.run("app_api_handler:app", host="0.0.0.0", port=port)
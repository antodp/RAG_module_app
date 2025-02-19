import uvicorn
import os
import boto3
import json
from fastapi import FastAPI
from mangum import Mangum
from pydantic import BaseModel
from rag_app.query_rag import QueryResponse, query_rag
from query_model import QueryModel

WORKER_LAMBDA_NAME = os.environ.get("WORKER_LAMBDA_NAME", None)

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

    # create the query item and put it into the db
    new_query = QueryModel(query_text=request.query_text)

    if WORKER_LAMBDA_NAME:
        # make an async call to the worker (RAG/AI app)
        new_query.put_item()
        invoke_worker(new_query)
    else:
        # make a synchronous call to the worker (the RAG/AI app)
        query_response = query_rag(request.query_text)
        new_query.answer_text = query_response.response_text
        new_query.sources = query_response.sources
        new_query.is_complete = True
        new_query.put_item()
    
    return new_query

def invoke_worker(query: QueryModel):
    # init Lambda client
    lambda_client = boto3.client("lambda")

    # get QueryModel as dictionary, thanks to pydantic
    payload = query.model_dump()

    # Invoke another Lambda function asynchronously
    response = lambda_client.invoke(
        FunctionName=WORKER_LAMBDA_NAME,
        InvocationType="Event",
        Payload=json.dumps(payload),
    )

    print(f"✅ Worker Lambda invoked: {response}")

if __name__ == "__main__":
    port = 8000
    print(f"Running the FastAPI server on port {port}.")
    uvicorn.run("app_api_handler:app", host="0.0.0.0", port=port)
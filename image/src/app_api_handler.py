import uvicorn
from fastapi import FastAPI
from mangum import Mangum
from pydantic import BaseModel
from rag_app.query_rag import QueryResponse, query_rag

app = FastAPI()
handler = Mangum(app)  # entry point for AWS Lambda

class SubmitQueryRequest(BaseModel):
    query_text: str

@app.get("/")
def index():
    return {"Hello": "World"}

@app.post("/submit_query")
def submit_query_endpoint(requests: SubmitQueryRequest) -> QueryResponse:
    query_response = query_rag(requests.query_text)
    return query_response

if __name__ == "__main__":
    port = 8000
    print(f"Running the FastAPI server on port {port}.")
    uvicorn.run("app_api_handler:app", host="0.0.0.0", port=port)
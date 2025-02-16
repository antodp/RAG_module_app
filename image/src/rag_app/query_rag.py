from dataclasses import dataclass
from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrock
from rag_app.get_chroma_db import get_chroma_db

# Generalized Prompt (No Regulatory-Specific Language)
PROMPT_TEMPLATE = """
Answer the question **only using the provided context**:

{context}

---
If the answer cannot be found in the retrieved context, respond with: "I don't know.". YET, if the context doesn't provide enough information but you can generalize the question from it and give significant, closest information, please do.

Frame your response clearly and concisely, ensuring it is structured and directly addresses the question.

Do not infer additional information beyond what is provided in the context.

---
**Question:** {question}
**Answer:**
"""

BEDROCK_MODEL_ID = "mistral.mistral-7b-instruct-v0:2"


@dataclass
class QueryResponse:
    query_text: str
    response_text: str
    sources: List[str]


def query_rag(query_text: str) -> QueryResponse:
    db = get_chroma_db()

    # Search the DB.
    # Retrieve relevant chunks using Max Marginal Relevance (MMR) search
    results = db.max_marginal_relevance_search(query_text, k=5, fetch_k=15, lambda_mult=0.1)
    context_text = "\n\n---\n\n".join([doc.page_content for doc in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    print(prompt)

    model = ChatBedrock(model_id=BEDROCK_MODEL_ID)
    response = model.invoke(prompt)
    response_text = response.content

    sources = [doc.metadata.get("id", None) for doc in results]
    print(f"Response: {response_text}\nSources: {sources}")

    return QueryResponse(
        query_text=query_text, response_text=response_text, sources=sources
    )


if __name__ == "__main__":
    query_rag("What percentage of people affected by LFH suffer from macrodactyly? Also, in what race does it occur more often?")
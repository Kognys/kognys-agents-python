from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from kognys.config import powerful_llm
from kognys.graph.state import KognysState
from kognys.utils.transcript import append_entry

class RefinedQueries(BaseModel):
    """A set of search queries optimized for different academic APIs."""
    openalex_query: str = Field(description="An optimized search query for the OpenAlex API, using keyword-based search.")
    semantic_scholar_query: str = Field(description="An optimized search query for the Semantic Scholar API, using boolean operators, exact phrases, and field filters like 'year'.")
    arxiv_query: str = Field(description="An optimized search query for the arXiv API, using field prefixes like 'ti:', 'au:', 'abs:', and boolean operators like 'AND', 'OR', 'ANDNOT'.")

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert research librarian. Your task is to take a user's research question and reformulate it into three optimized queries, one for each of the following academic search APIs: OpenAlex, Semantic Scholar, and arXiv.

            **API Query Guidelines:**

            1.  **OpenAlex:**
                -   Uses a general `search` parameter that covers titles, abstracts, and full text.
                -   Focus on clear, concise keywords. Boolean operators (AND, OR, NOT) are supported.
                -   Example: `(synthetic biology) AND (genome engineering OR CRISPR)`

            2.  **Semantic Scholar:**
                -   Supports advanced syntax like `+` (AND), `|` (OR), `-` (NOT), and `*` (wildcard).
                -   Use quotation marks `""` for exact phrases.
                -   Can filter by year range, e.g., `year:2023-`.
                -   Example: `"synthetic biology" + (developments | advancements) year:2023-`

            3.  **arXiv:**
                -   Uses field prefixes: `ti:` (title), `abs:` (abstract), `au:` (author), `all:` (all fields).
                -   Boolean operators are `AND`, `OR`, `ANDNOT`.
                -   Group expressions with parentheses `()`.
                -   Example: `abs:("synthetic biology" OR "genetic engineering") AND ti:(developments OR advancements)`

            Based on these rules, generate the three distinct, optimized queries. You must respond using the `RefinedQueries` JSON format.
            """
        ),
        ("human", "User's research question: {question}"),
    ]
)

def node(state: KognysState) -> dict:
    """
    Refines the user's question into optimized queries for each academic API.
    """
    # FIX: Use attribute access instead of .get()
    question = state.validated_question
    if not question:
        raise ValueError("Validated question is missing from state.")

    print(f"---QUERY REFINER: Optimizing query for '{question}'---")

    structured_llm = powerful_llm.with_structured_output(RefinedQueries)
    chain = _PROMPT | structured_llm
    response = chain.invoke({"question": question})

    refined_queries = {
        "openalex": response.openalex_query,
        "semantic_scholar": response.semantic_scholar_query,
        "arxiv": response.arxiv_query
    }

    print("---QUERY REFINER: Generated Optimized Queries---")
    for api, query in refined_queries.items():
        print(f"  - [{api.capitalize()}]: {query}")

    return {
        "refined_queries": refined_queries,
        "transcript": append_entry(
            state.transcript,
            agent="QueryRefiner",
            action="Refined search queries",
            details=f"Generated {len(refined_queries)} queries"
        )
    }
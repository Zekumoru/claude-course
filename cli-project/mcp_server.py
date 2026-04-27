from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

mcp = FastMCP("DocumentMCP", log_level="ERROR")


docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

@mcp.tool(
    name="read_doc_contents",
    description="Read the contents of a document and return it as a string."
)
def read_document(
    doc_id: str = Field(description="Id of the document to read.")
):
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found.")
    
    return docs[doc_id]

@mcp.tool(
    name="edit_document",
    description="Edit a document by replacing a string in the document's content with a new string."
)
def edit_document(
    doc_id: str = Field(description="Id of the document that will be edited."),
    old_str: str = Field(description="The text to replace. Must match exactly, including whitespace."),
    new_str: str = Field(description="The new text to insert in place of the old text.")
):
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found.")
    
    docs[doc_id] = docs[doc_id].replace(old_str, new_str)


@mcp.resource(
    "docs://documents",
    mime_type="application/json"
)
def list_docs() -> list[str]:
    return list(docs.keys())


@mcp.resource(
    "docs://documents/{doc_id}",
    mime_type="text/plain"
)
def fetch_doc(doc_id: str) -> str:
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    return docs[doc_id]


@mcp.prompt(
    name="format",
    description="Rewrites the contents of a document in markdown format."
)
def format_document(
    doc_id: str = Field(description="Id of the document to format.")
) -> list[base.Message]:
    prompt = f"""
    Reformat the document using clean, well-structured Markdown.

    Document ID:
    {doc_id}

    Improve readability by adding appropriate Markdown syntax, such as headings, bullet points,
    numbered lists, tables, emphasis, and code blocks where useful.

    Preserve the original meaning and content. Do not add unrelated information.
    Use the `edit_document` tool to apply the formatting changes to the document.
    """

    return [
        base.UserMessage(prompt)
    ]


@mcp.prompt(
    name="summarize",
    description="Summarizes the contents of a document."
)
def summarize_document(
    doc_id: str = Field(description="Id of the document to summarize.")
) -> list[base.Message]:
    prompt = f"""
    Summarize the contents of the document clearly and concisely.

    Document ID:
    {doc_id}

    Focus on the main ideas, key details, and important conclusions.
    Preserve the original meaning and avoid adding information that is not present in the document.
    """

    return [
        base.UserMessage(prompt)
    ]


if __name__ == "__main__":
    mcp.run(transport="stdio")

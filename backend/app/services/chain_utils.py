from __future__ import annotations

from typing import Any

from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate


class ChainExecutionError(RuntimeError):
    """Raised when a structured chain cannot return valid output."""


def _response_to_text(response: object) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, list):
        return "\n".join(str(item) for item in content)
    return str(content)


def invoke_structured_chain(
    *,
    llm: Any,
    prompt: ChatPromptTemplate,
    parser: PydanticOutputParser,
    input_data: dict[str, object],
    parser_max_retries: int,
) -> object:
    payload = {**input_data, "format_instructions": parser.get_format_instructions()}

    last_error: Exception | None = None
    text = ""
    for _ in range(max(1, parser_max_retries + 1)):
        try:
            rendered_prompt = prompt.format_prompt(**payload).to_string()
            response = llm.invoke(rendered_prompt)
            text = _response_to_text(response)
            return parser.parse(text)
        except Exception as exc:
            last_error = exc
            try:
                fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=llm)
                return fixing_parser.parse(text)
            except Exception as fix_exc:
                last_error = fix_exc

    raise ChainExecutionError(f"Structured chain failed after retries: {last_error}")

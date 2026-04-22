# Load env variables
from dotenv import load_dotenv
load_dotenv()

# Create an API client
from anthropic import Anthropic

CLAUDE_HAIKU = "claude-haiku-4-5"
CLAUDE_SONNET = "claude-sonnet-4-6"

client = Anthropic()
model = CLAUDE_SONNET

# Create API helper functions
from typing import TypedDict, Required, NotRequired
from anthropic.types import MessageParam

def add_user_message(messages: list[MessageParam], text: str):
    user_message: MessageParam = { "role": "user", "content": text }
    messages.append(user_message)


def add_assistant_message(messages: list[MessageParam], text: str):
    assistant_message: MessageParam = { "role": "assistant", "content": text }
    messages.append(assistant_message)


class CreateMessageParams(TypedDict):
    model: Required[str]
    max_tokens: Required[int]
    messages: Required[list[MessageParam]]
    system: NotRequired[str]
    temperature: NotRequired[int]
    stop_sequences: NotRequired[list[str]]

def chat(messages: list[MessageParam], model: str = model, system: str | None = None, temperature: int | None = None, stop_sequences: list[str] | None = None) -> str:
    params: CreateMessageParams = {
        "model": model,
        "max_tokens": 1024,
        "messages": messages
    }

    if system:
        params["system"] = system

    if temperature:
        params["temperature"] = temperature

    if stop_sequences:
        params["stop_sequences"] = stop_sequences

    response = client.messages.create(**params)

    return response.content[0].text


import json

def generate_dataset():
    prompt = """
Generate an evaluation dataset for a prompt evaluation. The dataset will be used to evaluate prompts that generate Python, JSON, or Regex specifically for AWS-related tasks. Generate an array of JSON objects, each representing task that requires Python, JSON, or a Regex to complete.

Example output:
```json
[
{
    "task": "Description of task",
    "format": "json" or "python" or "regex",
    "solution_criteria": "Key criteria for evaluating the solution"
},
...additional
]
```

* Focus on tasks that can be solved by writing a single Python function, a single JSON object, or a single regex
* Focus on tasks that do not require writing much code

Please generate 3 objects.
"""

    messages: list[MessageParam] = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, "```json")
    text = chat(messages, model=CLAUDE_HAIKU, stop_sequences=["```"])
    dataset = json.loads(text)

    with open('dataset.json', 'w') as f:
        json.dump(dataset, f, indent=2)
        print("Dataset generated.")


from typing import Literal

class TestCase(TypedDict):
    task: str
    format: Literal["json", "python", "regex"]
    solution_criteria: str

def run_prompt(test_case: TestCase):
    """Merges the prompt and test case input, then returns the result."""
    prompt = f"""
Please solve the following task:

{test_case["task"]}

* Respond only with Python, JSON, or a plain Regex
* Do not add any comments or commentary or explanation
"""

    messages: list[MessageParam] = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, "```code")
    output = chat(messages, model=CLAUDE_HAIKU, stop_sequences=["```"])
    return output


class ModelGrade(TypedDict):
    strengths: list[str]
    weaknesses: list[str]
    reasoning: str
    score: float

def grade_by_model(test_case: TestCase, response: str) -> ModelGrade:
    # Create evaluation prompt
    eval_prompt = f"""
You are an expert code reviewer. Evaluate this AI-generated solution.

Task:
<task>
{test_case['task']}
</task>

Solution:
<solution>
{response}
</solution>

Criteria you should use to evaluate the solution:
<criteria>
{test_case['solution_criteria']}
</criteria>

Provide your evaluation as a structured JSON object with:
- "strengths": An array of 1-3 key strengths
- "weaknesses": An array of 1-3 key areas for improvement  
- "reasoning": A concise explanation of your assessment
- "score": A number between 1-10, can be two point decimal

Respond with JSON. Keep your response concise and direct.
Example response shape:
{{
    "strengths": string[],
    "weaknesses": string[],
    "reasoning": string,
    "score": number
}}
"""
    
    messages: list[MessageParam] = []
    add_user_message(messages, eval_prompt)
    add_assistant_message(messages, "```json")
    
    eval_text = chat(messages, model=CLAUDE_HAIKU, stop_sequences=["```"])
    return json.loads(eval_text)


def validate_json(text: str):
    try:
        json.loads(text.strip())
        return 10
    except json.JSONDecodeError:
        return 0


import ast

def validate_python(text: str):
    try:
        ast.parse(text.strip())
        return 10
    except SyntaxError:
        return 0


import re

def validate_regex(text: str):
    try:
        re.compile(text.strip())
        return 10
    except re.error:
        return 0


def grade_by_syntax(test_case: TestCase, output: str):
    format = test_case["format"]

    if format == "json":
        return validate_json(output)
    elif format == "python":
        return validate_python(output)
    else:
        return validate_regex(output)


class TestResult(TypedDict):
    output: str
    test_case: TestCase
    score: float
    reasoning: str

def run_test_case(test_case: TestCase) -> TestResult:
    """Calls run_prompt, then grades the result"""
    output = run_prompt(test_case)

    model_grade = grade_by_model(test_case, output)
    model_score = model_grade["score"]
    reasoning = model_grade["reasoning"]

    syntax_score = grade_by_syntax(test_case, output)

    score = (model_score + syntax_score) / 2

    return {
        "output": output,
        "test_case": test_case,
        "score": score,
        "reasoning": reasoning
    }


from statistics import mean

def run_eval(dataset: list[TestCase]) -> list[TestResult]:
    """Loads the dataset and calls run_test_case with each case"""
    results: list[TestResult] = []

    for test_case in dataset:
        result = run_test_case(test_case)
        results.append(result)

    average_score = mean(result["score"] for result in results)
    print(f"Average score: {average_score}")

    return results

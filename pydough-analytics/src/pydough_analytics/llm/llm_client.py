import re
from datetime import datetime
import pydough
from ..utils.utils import extract_python_code, execute_code_and_extract_result
from ..utils.file_service import load_markdown
from .ai_providers import get_provider


# This class represents the result of an LLM query, encapsulating the code, explanation, DataFrame, exception, original question, and SQL output.
class Result:
    def __init__(
        self, 
        pydough_code=None, 
        full_explanation=None, 
        df=None, 
        exception=None, 
        original_question=None, 
        sql_output=None,
    ):
        self.code = pydough_code
        self.full_explanation = full_explanation
        self.df = df
        self.exception = exception
        self.original_question = original_question
        self.sql = sql_output
        
    def to_dict(self):
        return {
            "code": self.code,
            "sql": self.sql,
            "df": self.df.to_dict(orient="records") if self.df is not None else None,
            "full_explanation": self.full_explanation,
            "exception": self.exception,
            "original_question": self.original_question,
        }

# This class serves as a client for interacting with an LLM to ask questions, handle discourse, and correct errors.
class LLMClient:
    def __init__(self, prompt, script, db_markdown_map=None, provider="google", model="gemini-2.5-pro", definitions=None):
        self.prompt = prompt
        self.script = script
        self.db_markdown_map = db_markdown_map or {}
        self.provider = provider
        self.model = model
        self.definitions = definitions or []

    # This method asks a question to the LLM, formats the prompt, executes the code, and returns a Result object.
    def ask(self, question, kg_path, db_config, md_path, db_name, context_data=None, auto_correct=False, max_corrections=1, **kwargs):
        result = Result(original_question=question)

        try:
            md_content = load_markdown(md_path)
            self.db_markdown_map[db_name] = md_content
            # Ejecutar prompt con proveedor
            client = get_provider(self.provider, self.model)
            formatted_q, formatted_prompt = self.format_prompt(question, db_name, context_data)

            response = client.ask(formatted_q, formatted_prompt, **kwargs)
            raw_response = response[0] if isinstance(response, tuple) else response 
            extracted_code = extract_python_code(raw_response)

            cleaned_explanation = re.sub(r"```python\n.*?```", "", raw_response, flags=re.DOTALL).strip()
            pretty_explanation = "\n\n".join([line.strip() for line in cleaned_explanation.split("\n") if line.strip()])
            
            result.code = extracted_code
            result.full_explanation = pretty_explanation
            result.df = None
            result.sql = None
            
            env = {"pydough": pydough, "datetime": datetime} 

            df, sql = execute_code_and_extract_result(
                extracted_code,
                env,
                db_name=db_name,
                db_config=db_config,
                kg_path=kg_path
            )
            
            result.df = df
            result.sql = sql

        except Exception as e:
            result.exception = str(e) 

            if auto_correct and max_corrections > 0:
                return self.correct(
                    result,
                    db_name=db_name,
                    kg_path=kg_path,
                    db_config=db_config,
                    md_path=md_path,
                    context_data=context_data,
                    auto_correct=auto_correct,
                    max_corrections=max_corrections - 1,
                    **kwargs
                )

        return result


    # This method adds a new definition to the LLM client, which can be used in prompts.
    def add_definition(self, new_definition):
        if new_definition:
            self.definitions.append(new_definition)

    # This method reformulates a follow-up question based on the original question and the result of a previous query.
    def discourse(self, result, follow_up):
        if not result:
            return follow_up
        elif not result.code:
            return (
                f"This was the original question: '{result.original_question}', but due to a previous issue, "
                f"the system couldn't generate a valid answer or code for it. "
                f"Now, answer this follow-up question: '{follow_up}'. "
                f"IMPORTANT: If you need any of the above code, you must declare it again because it does not exist in memory."
            )
        return (
            f"You solved this question: {result.original_question}. using this code: {result.code}. "
            f"The dataframe generated was: {result.df}. Now, answer this follow-up question: '{follow_up}'. "
            f"IMPORTANT: If you need any of the above code, you must declare it again because it does not exist in memory."
        )

    # This method corrects the result of a previous query if an exception occurred, reformulating the question to ask for help.
    def correct(self, result, kg_path, db_config, md_path, db_name, context_data, **kwargs):
        if result.exception:
            try:
                formatted_q, formatted_prompt = self.format_prompt(result.original_question, db_name, context_data)
                corrective_question = (
                    f"An error occurred while processing this code: {result.code}. "
                    f"The error is: '{result.exception}'. The original question was: '{result.original_question}'. "
                    f"Can you help me fix the issue? Take into account the context: '{formatted_prompt}'."
                )
                return self.ask(corrective_question, db_name=db_name, kg_path=kg_path, db_config=db_config, md_path=md_path, context_data=context_data, **kwargs)
            except Exception as e:
                return Result(original_question=result.original_question, exception=str(e))
        return result
    
         # This method formats the prompt for the LLM, including the question, database schema, and any additional context.
    def format_prompt(self, question, db_name, context_data):
        db_content = self.db_markdown_map.get(db_name, "")
        context = context_data or {}
        recommendation = context.get("context_id", "")
        similar_code = context.get("similar_queries", "")
        redefined_question = context.get("redefined_question", question)    
        formatted_q = f"{redefined_question}\nDatabase Schema:\n{str(db_content)}"
        formatted_prompt = self.prompt.format(
            script_content=self.script,
            database_content=str(db_content),
            similar_queries=similar_code,
            recomendation=recommendation,
            definitions="".join(self.definitions)
        )
        return formatted_q, formatted_prompt 

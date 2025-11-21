import pydough
from pydough.metadata import GraphMetadata
from pydough.unqualified import UnqualifiedNode
from pydough import PyDoughSession
import re 
import pandas as pd


class SQLResult: 
    def __init__(self, sql: str, exception=None):
        self.sql = sql
        self.is_valid = exception is None
        self.exception = exception

class Pydough_helper:
    def __init__(self, metadata_path: str, database_name: str):
        self.session : PyDoughSession = pydough.PyDoughSession()
        self.metadata : GraphMetadata = self.session.load_metadata_graph(metadata_path, database_name)
        #self.session.connect_database("sqlite", database= f"{}{database_name}.sqlite")
        
    def generate_sql(self, pydough_code: str):            
        response_var = extract_var(pydough_code)                     
        try:
            query : UnqualifiedNode = pydough.from_string(pydough_code, metadata=self.session.metadata, answer_variable=response_var)         
            sql = pydough.to_sql(query, metadata=self.session.metadata, config=self.session.config, database=self.session.database)         
            return SQLResult(sql)
        except Exception as e:
            return SQLResult(None, exception=e)
    
    def generate_dataframe(self, pydough_code: str):
        query : UnqualifiedNode = pydough.from_string(pydough_code, metadata=self.session.metadata)
        df = pydough.to_df(query, metadata=self.session.metadata, config=self.session.config, database=self.session.database)
        return df
    
    def generate_text_graphic_explanation(self, pydough_code: str):            
        response_var = extract_var(pydough_code)                     
        try:
            query : UnqualifiedNode = pydough.from_string(pydough_code, metadata=self.session.metadata, answer_variable=response_var)         
            text_graphic_explanation = pydough.explain(query, metadata=self.session.metadata, config=self.session.config, database=self.session.database)         
            return text_graphic_explanation
        except Exception as e:
            return None


def stringify_dataframe(df, max_rows: int = 100, max_chars: int = 10000) -> str:
    """Return a readable, bounded string of a DataFrame using pandas' to_string.
    Includes shape and columns header plus a head sample. Truncates to max_chars.
    """
    if df is None:
        return "<df=None>"
    try:
        head = df.head(max_rows)
        header = f"shape={tuple(df.shape)} columns={list(map(str, df.columns))}"
        body = head.to_string(index=False)
        string_df = f"{header}\n{body}"
        if len(string_df) > max_chars:
            string_df = string_df[:max_chars] + "\n...TRUNCATED..."
        return string_df
    except Exception as e:
        return f"<df=unserializable error={e}>"

def extract_var(sql_str: str):

    sql_str = sql_str.replace('\n', ' ').strip()
    depth = 0
    assignments = []
    
    for i, char in enumerate(sql_str):
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == '=' and depth == 0:
            before_equals = sql_str[:i].strip()
            var_match = re.search(r'(\w+)\s*$', before_equals)
            if var_match:
                assignments.append(var_match.group(1))
    
    return assignments[-1] if assignments else None           

    
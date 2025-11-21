from threading import Thread
from queue import Queue
import pandas as pd
import sqlite3
import hashlib
import os
from pathlib import Path
import fcntl
import pickle


class SqliteCache:
    
    """ Init example: cache = SqliteCache("./sql_cache", False, timeout=600) """
    
    def __init__(self, cache_path: str, read_only: bool = False, timeout: float = 300):
        self.cache_path = cache_path
        self.read_only = read_only
        self.timeout = timeout
        Path(cache_path).mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, database_path: str, sql: str):
        cache_string = f"{database_path}|{sql.strip()}"
        return hashlib.md5(cache_string.encode('utf-8')).hexdigest()
    
    def _get_cache_file(self, cache_key: str):
        return os.path.join(self.cache_path, f"{cache_key}.pkl")
    
    def _get_lock_file(self, data_file: str):
        return data_file + '.lock'
    
    def _save_to_cache(self, cache_key: str, df: pd.DataFrame):
        data_file = self._get_cache_file(cache_key)
        lock_file_path = self._get_lock_file(data_file)
        
        with open(lock_file_path, 'w') as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            with open(data_file, "wb") as f:
                pickle.dump(df, f)          
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        if os.path.exists(lock_file_path):
            os.remove(lock_file_path)
    
    def _load_from_cache(self, cache_key: str):
        
        data_file = self._get_cache_file(cache_key)    
        lock_file_path = self._get_lock_file(data_file)

        if not os.path.exists(data_file):
            return None
        
        with open(lock_file_path, 'w') as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_SH)
            with open(data_file, "rb") as f:
                df = pickle.load(f) 
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        
        if os.path.exists(lock_file_path):
            os.remove(lock_file_path)
        
        return df
    
    def execute(self, database_path: str, sql: str):
        cache_key = self._get_cache_key(database_path, sql)
        cached_df = self._load_from_cache(cache_key)
        
        if cached_df is not None:
            print("Cache found for query")
            return cached_df
        
        print(f"Cache not found for query")
        df = convert_sql_to_dataframe(
            database_path, 
            sql, 
            query_timeout=self.timeout,
            block_timeout=self.timeout
        )
        
        if not self.read_only:
            self._save_to_cache(cache_key, df)
        
        return df
    
    
def _execute_query_in_thread(db_path: str, sql_query: str, block_timeout:float, result_queue: any):
    try:
        with sqlite3.connect(f'file:{db_path}?mode=ro', uri=True, timeout=block_timeout) as conn:
            df = pd.read_sql_query(sql_query, conn)
        result_queue.put(('success', df))
    except Exception as e:
        result_queue.put(('error', str(e)))

def convert_sql_to_dataframe(db_path: str, sql_query: str, query_timeout: float, block_timeout: float = 5.0) -> pd.DataFrame:
    result_queue = Queue()
    thread = Thread(
        target=_execute_query_in_thread,
        args=(db_path, sql_query, block_timeout, result_queue)
    )
    
    thread.daemon = True
    thread.start()
    thread.join(timeout=query_timeout)
    
    if thread.is_alive():
        return pd.DataFrame({"Exec_error": ["Execution timed out"]})
    
    if not result_queue.empty():
        status, data = result_queue.get()
        if status == 'success':
            return data
        else:
            return pd.DataFrame({"Exec_error": [data]})
    
    return pd.DataFrame({"Exec_error": ["Process ended without result"]})

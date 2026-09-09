from sqlalchemy import create_engine, inspect
import pandas as pd

class DBManager:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = create_engine(connection_string)
        self.inspector = inspect(self.engine)
        
    def get_schemas(self):
        try:
            schemas = self.inspector.get_schema_names()
            return schemas if schemas else ['default']
        except Exception:
            return ['default']
            
    def get_tables(self, schema=None):
        if schema == 'default':
            schema = None
        return self.inspector.get_table_names(schema=schema)
        
    def get_columns(self, table_name, schema=None):
        if schema == 'default':
            schema = None
        return self.inspector.get_columns(table_name, schema=schema)
        
    def fetch_sample_data(self, table_name, schema=None, sample_size=50000):
        if schema == 'default':
            schema = None
            
        table_path = f"{schema}.{table_name}" if schema else table_name
        
        # Uso do pandas para leitura
        # Em bancos grandes o pd.read_sql_table seria lento, então usamos limit (ou TOP no SQL Server).
        if self.engine.dialect.name == 'mssql':
            query = f"SELECT TOP {sample_size} * FROM {table_path}"
        elif self.engine.dialect.name == 'oracle':
            query = f"SELECT * FROM {table_path} FETCH FIRST {sample_size} ROWS ONLY"
        else:
            query = f"SELECT * FROM {table_path} LIMIT {sample_size}"
        
        try:
            df = pd.read_sql(query, self.engine)
            return df
        except Exception as e:
            raise RuntimeError(f"Erro ao ler amostra da tabela {table_path}: {str(e)}")

# File: db_management_system/database/db_manager.py
import pickle  # Import the pickle library
import os      # Import os for path manipulation
from .table import Table # Import the Table class

class DatabaseManager:
    """
    Manages multiple databases, each containing several Tables.
    Provides methods to create, delete, and list databases and tables.
    """
    def __init__(self):
        """Initializes the DatabaseManager with an empty dictionary to hold databases."""
        self.databases = {}  # Structure: {db_name: {table_name: Table_instance}}
        print("Database Manager initialized.")

    def create_database(self, db_name):
        """
        Creates a new, empty database container.

        Args:
            db_name (str): The name for the new database.

        Returns:
            tuple: (None, True) on success, (error_message, False) on failure.
        """
        if not isinstance(db_name, str) or not db_name:
            return "Database name must be a non-empty string.", False
        if db_name in self.databases:
            return f"Database '{db_name}' already exists.", False

        self.databases[db_name] = {} # Initialize with an empty dict for tables
        print(f"Database '{db_name}' created successfully.")
        return None, True

    def delete_database(self, db_name):
        """
        Deletes an existing database and all its tables.

        Args:
            db_name (str): The name of the database to delete.

        Returns:
            tuple: (None, True) on success, (error_message, False) if database not found.
        """
        if db_name not in self.databases:
            return f"Database '{db_name}' not found.", False

        del self.databases[db_name]
        print(f"Database '{db_name}' deleted successfully.")
        return None, True

    def list_databases(self):
        """
        Lists the names of all created databases.

        Returns:
            tuple: (list_of_db_names, True)
        """
        db_names = list(self.databases.keys())
        print(f"Available databases: {db_names}")
        return db_names, True

    def create_table(self, db_name, table_name, schema, order=8, search_key=None):
        """
        Creates a new table within a specified database.

        Args:
            db_name (str): The name of the database to add the table to.
            table_name (str): The name for the new table.
            schema (dict): The schema definition for the table.
            order (int): The B+ Tree order for the table's index.
            search_key (str): The column name to use as the B+ Tree index key.

        Returns:
            tuple: (None, True) on success, (error_message, False) on failure.
        """
        if db_name not in self.databases:
            return f"Database '{db_name}' not found.", False
        if not isinstance(table_name, str) or not table_name:
            return "Table name must be a non-empty string.", False
        if table_name in self.databases[db_name]:
            return f"Table '{table_name}' already exists in database '{db_name}'.", False

        try:
            # Create the Table instance (constructor handles schema/key validation)
            new_table = Table(name=table_name, schema=schema, order=order, search_key=search_key)
            self.databases[db_name][table_name] = new_table
            print(f"Table '{table_name}' created in database '{db_name}'.")
            return None, True
        except ValueError as ve: # Catch validation errors from Table constructor
            return f"Failed to create table '{table_name}': {ve}", False
        except Exception as e: # Catch other unexpected errors
            return f"An unexpected error occurred creating table '{table_name}': {e}", False

    def delete_table(self, db_name, table_name):
        """
        Deletes a table from a specified database.

        Args:
            db_name (str): The name of the database containing the table.
            table_name (str): The name of the table to delete.

        Returns:
            tuple: (None, True) on success, (error_message, False) on failure.
        """
        if db_name not in self.databases:
            return f"Database '{db_name}' not found.", False
        if table_name not in self.databases[db_name]:
            return f"Table '{table_name}' not found in database '{db_name}'.", False

        del self.databases[db_name][table_name]
        print(f"Table '{table_name}' deleted from database '{db_name}'.")
        return None, True

    def list_tables(self, db_name):
        """
        Lists the names of all tables within a specified database.

        Args:
            db_name (str): The name of the database to inspect.

        Returns:
            tuple: (list_of_table_names, True) on success, (error_message, False) if db not found.
        """
        if db_name not in self.databases:
            return f"Database '{db_name}' not found.", False

        table_names = list(self.databases[db_name].keys())
        print(f"Tables in database '{db_name}': {table_names}")
        return table_names, True

    def get_table(self, db_name, table_name):
        """
        Retrieves a Table object instance for direct interaction.

        Args:
            db_name (str): The name of the database.
            table_name (str): The name of the table.

        Returns:
            tuple: (Table_instance, True) on success, (None, False) if db or table not found.
        """
        if db_name not in self.databases:
            # print(f"Error getting table: Database '{db_name}' not found.")
            return None, False
        table_instance = self.databases[db_name].get(table_name) # Use .get for safe access
        if table_instance is None:
            # print(f"Error getting table: Table '{table_name}' not found in database '{db_name}'.")
            return None, False

        return table_instance, True
    
    # --- task 6 NEW Persistence Methods ---

    def save_to_disk(self, filepath):
        """
        Saves the entire state of the Database Manager (all databases and tables)
        to a file using pickle.

        Args:
            filepath (str): The path to the file where the data should be saved.

        Returns:
            tuple: (None, True) on success, (error_message, False) on failure.
        """
        try:
            # Ensure directory exists
            dir_name = os.path.dirname(filepath)
            if dir_name: # Check if directory part exists in the path
                os.makedirs(dir_name, exist_ok=True)

            # Open the file in binary write mode ('wb')
            with open(filepath, 'wb') as f:
                # Dump the self.databases dictionary into the file
                pickle.dump(self.databases, f, pickle.HIGHEST_PROTOCOL)
            print(f"Database state successfully saved to '{filepath}'.")
            return None, True
        except (pickle.PicklingError, OSError, IOError, Exception) as e:
            error_msg = f"Failed to save database state to '{filepath}': {e}"
            print(error_msg)
            return error_msg, False

    def load_from_disk(self, filepath):
        """
        Loads the Database Manager state from a previously saved pickle file.
        This will overwrite the current state in self.databases.

        Args:
            filepath (str): The path to the file from which to load the data.

        Returns:
            tuple: (None, True) on success, (error_message, False) on failure.
        """
        try:
            # Check if file exists before attempting to open
            if not os.path.exists(filepath):
                return f"Load failed: File not found at '{filepath}'.", False

            # Open the file in binary read mode ('rb')
            with open(filepath, 'rb') as f:
                # Load the data (should be the dictionary) from the file
                loaded_data = pickle.load(f)

            # Basic validation: Check if loaded data is a dictionary
            if not isinstance(loaded_data, dict):
                 raise TypeError("Loaded data is not in the expected dictionary format.")

            # Restore the state
            self.databases = loaded_data
            print(f"Database state successfully loaded from '{filepath}'.")
            # Optional: You might want to print loaded databases/tables here for confirmation
            # self.list_databases()
            # for db_name in self.databases:
            #     self.list_tables(db_name)
            return None, True
        except FileNotFoundError: # Already handled by os.path.exists, but good practice
            error_msg = f"Load failed: File not found at '{filepath}'."
            print(error_msg)
            return error_msg, False
        except (pickle.UnpicklingError, EOFError, TypeError, ImportError, Exception) as e:
            # Catch various errors during loading/unpickling
            error_msg = f"Failed to load database state from '{filepath}': {e}"
            print(error_msg)
            # Optionally reset state if load fails badly
            # self.databases = {}
            return error_msg, False
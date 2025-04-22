# File: db_management_system/database/table.py

from .bplustree import BPlusTree  # Import the BPlusTree implementation

class Table:
    """
    Represents a table in the database, using a B+ Tree for indexing.
    Stores records as dictionaries and uses a specified search_key for the B+ Tree.
    """
    def __init__(self, name, schema, order=8, search_key=None):
        """
        Initializes a new Table.

        Args:
            name (str): The name of the table.
            schema (dict): Dictionary defining column names and their expected types
                           (e.g., {"id": int, "name": str}).
            order (int): The order for the underlying B+ Tree index.
            search_key (str): The column name from the schema to be used as the
                              primary key for the B+ Tree index. Must be provided.
        """
        if not isinstance(name, str) or not name:
            raise ValueError("Table name must be a non-empty string.")
        if not isinstance(schema, dict) or not schema:
            raise ValueError("Schema must be a non-empty dictionary.")
        if not isinstance(order, int) or order < 3:
            raise ValueError("B+ Tree order must be an integer >= 3.")
        if search_key is None or not isinstance(search_key, str):
            raise ValueError("A search_key (string column name) must be provided.")
        if search_key not in schema:
            raise ValueError(f"search_key '{search_key}' not found in schema columns: {list(schema.keys())}")

        self.name = name
        self.schema = schema
        self.order = order
        self.search_key = search_key
        # The B+ Tree stores: key = record[search_key], value = entire record dictionary
        self.data = BPlusTree(order=self.order)
        print(f"Table '{self.name}' created with search key '{self.search_key}'.")

    def _validate_record(self, record):
        """
        Validates a record against the table's schema.

        Args:
            record (dict): The record dictionary to validate.

        Returns:
            bool: True if the record is valid, False otherwise.
            str: An error message if validation fails, None otherwise.
        """
        if not isinstance(record, dict):
            return False, "Record must be a dictionary."

        # Check for missing columns defined in schema
        for col_name in self.schema:
            if col_name not in record:
                return False, f"Record missing required column: '{col_name}'."

        # Check for extra columns not in schema (optional, can be strict or lenient)
        # for col_name in record:
        #     if col_name not in self.schema:
        #         return False, f"Record contains undefined column: '{col_name}'."

        # Check data types
        for col_name, expected_type in self.schema.items():
            if col_name in record: # Check only if column exists (allows partial updates later if needed)
                value = record[col_name]
                if not isinstance(value, expected_type):
                    # Allow int to be treated as float if expected type is float
                    if expected_type == float and isinstance(value, int):
                        continue # Treat int as valid float
                    return False, f"Incorrect type for column '{col_name}'. Expected {expected_type.__name__}, got {type(value).__name__}."

        # Check if search key exists in the record
        if self.search_key not in record:
             return False, f"Record must contain the search key field '{self.search_key}'."

        return True, None

    def insert(self, record):
        """
        Inserts a record into the table.

        Args:
            record (dict): A dictionary representing the row to insert.

        Returns:
            bool: True if insertion was successful, False otherwise.
            str: An error message if insertion failed, None otherwise.
        """
        is_valid, error_msg = self._validate_record(record)
        if not is_valid:
            # print(f"Insert failed for table '{self.name}': {error_msg}")
            return False, error_msg

        key = record.get(self.search_key) # Get the value of the search key field
        if key is None: # Should be caught by validation, but double-check
             msg = f"Search key '{self.search_key}' has None value in record."
             # print(f"Insert failed for table '{self.name}': {msg}")
             return False, msg

        # Check if key already exists (B+ Tree search is efficient)
        if self.data.search(key) is not None:
            msg = f"Duplicate key error: Record with {self.search_key} = {key} already exists."
            # print(f"Insert failed for table '{self.name}': {msg}")
            return False, msg

        # Insert the key and the entire record dictionary into the B+ Tree
        try:
            self.data.insert(key, record)
            # print(f"Inserted record with key {key} into table '{self.name}'.")
            return True, None
        except Exception as e:
            # Catch potential internal B+ Tree errors if any
            msg = f"Internal B+ Tree error during insert: {e}"
            # print(f"Insert failed for table '{self.name}': {msg}")
            return False, msg


    def get(self, record_id):
        """
        Retrieves a single record by its ID (the value corresponding to search_key).

        Args:
            record_id: The value of the search_key to look for.

        Returns:
            dict: The record dictionary if found, None otherwise.
            bool: True if found, False otherwise.
        """
        record_data = self.data.search(record_id)
        if record_data is not None:
            return record_data, True
        else:
            return None, False

    def get_all(self):
        """
        Retrieves all records from the table, ordered by the search key.

        Returns:
            list: A list of all record dictionaries stored in the table.
            bool: Always True (unless an internal error occurs, which is unlikely here).
        """
        # self.data.get_all() returns list of (key, value) tuples
        # We only want the values (which are the record dictionaries)
        all_records = [record for key, record in self.data.get_all()]
        return all_records, True

    def update(self, record_id, new_record_data):
        """
        Updates the record identified by record_id with new data.
        The search_key field itself cannot be updated via this method.

        Args:
            record_id: The value of the search_key identifying the record to update.
            new_record_data (dict): A dictionary containing the new data for the record.
                                    It MUST include the original search_key value.

        Returns:
            bool: True if the update was successful, False otherwise.
            str: An error message if update failed, None otherwise.
        """
        # 1. Check if record exists
        existing_record, found = self.get(record_id)
        if not found:
            msg = f"Record with {self.search_key} = {record_id} not found for update."
            return False, msg

        # 2. Validate the new data
        is_valid, error_msg = self._validate_record(new_record_data)
        if not is_valid:
            return False, f"Invalid new record data: {error_msg}"

        # 3. Ensure the search key is not being changed
        if new_record_data.get(self.search_key) != record_id:
            msg = f"Updating the search key ('{self.search_key}') is not allowed via update. Key must remain {record_id}."
            return False, msg

        # 4. Perform the update in the B+ Tree
        # B+ Tree update replaces the value associated with the key
        updated = self.data.update(record_id, new_record_data)

        if updated:
            return True, None
        else:
            # This case might happen if the key mysteriously disappears between search and update (unlikely in single thread)
            # Or if BPlusTree.update implementation has issues.
            return False, f"Internal B+ Tree error during update for key {record_id}."

    def delete(self, record_id):
        """
        Deletes a record from the table based on its record_id (search_key value).

        Args:
            record_id: The value of the search_key for the record to delete.

        Returns:
            bool: True if deletion was successful, False if the record was not found.
            str: An error message if deletion failed for other reasons, None otherwise.
        """
        deleted = self.data.delete(record_id)
        if deleted:
            return True, None
        else:
            msg = f"Record with {self.search_key} = {record_id} not found for deletion."
            return False, msg


    def range_query(self, start_value, end_value):
        """
        Retrieves records where the search_key falls within [start_value, end_value].

        Args:
            start_value: The minimum value for the search_key (inclusive).
            end_value: The maximum value for the search_key (inclusive).

        Returns:
            list: A list of record dictionaries matching the range criteria.
            bool: Always True (unless internal B+ Tree error).
        """
        # self.data.range_query returns list of (key, value) tuples
        matching_records = [record for key, record in self.data.range_query(start_value, end_value)]
        return matching_records, True
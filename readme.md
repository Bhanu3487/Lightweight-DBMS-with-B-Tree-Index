# Lightweight DBMS with B+ Tree Indexing

## 1. Introduction

This project implements a basic Database Management System (DBMS) in Python. It utilizes a B+ Tree data structure for efficient indexing of table data, enabling fast search, insertion, deletion, updates, and range queries. The project includes performance analysis comparing the B+ Tree approach with a simple brute-force (list-based) method and provides a web-based UI for interaction.

## 2. Setup and Usage

### Prerequisites

*   Python 3.7+
*   Graphviz executable installed and added to the system PATH ([https://graphviz.org/download/](https://graphviz.org/download/))

### Installation

1.  Clone or download this repository.
2.  Navigate to the project's root directory (`db_management_system`).
3.  Install required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

### Running the UI

To interact with the database using the web interface:

1.  Ensure you are in the project's root directory.
2.  Run the Streamlit application:
    ```bash
    streamlit run app.py
    ```
3.  A new tab should open in your web browser with the UI. Use the sidebar to manage databases/tables and the main area to perform operations on the selected table.
4. You can create your own database and tables or scroll down the side bar to find a heading called **persistance** which has the option to load a database file with 2 tables relavent to our project. You can update the database and save the database. You can check the changes persist in the local database as well by running the code in part 3 and 4 under Visualization section(4) in report.

### Running Benchmarks & Analysis

The performance analysis and detailed demonstrations are available in the Jupyter Notebook:

1.  Ensure Jupyter Notebook or Jupyter Lab is installed (`pip install notebook` or `pip install jupyterlab`).
2.  Navigate to the project's root directory.
3.  Run Jupyter: `jupyter notebook` or `jupyter lab`.
4.  Open the `report.ipynb` file in your browser.
5.  Run the cells sequentially to execute the benchmarks and view the results (tables and plots).

## 3. File Structure

```
db_management_system/
├── database/                 # Core database logic
│   ├── __init__.py           # Makes 'database' a Python package
│   ├── bplustree.py          # B+ Tree implementation (Nodes, Tree logic)
│   ├── table.py              # Table class (uses B+ Tree for index)
│   ├── db_manager.py         # Manages Databases and Tables, Persistence
│   ├── bruteforce.py         # Simple list-based DB for comparison
│   └── performance.py        # Performance analysis and benchmarking class
├── saved_data/              # Default directory for saved database state
│   └── *.pkl                 # Saved database files
├── .gitignore               # Specifies intentionally untracked files for Git
├── app.py                   # Streamlit UI application script
├── report.ipynb             # Jupyter Notebook for analysis, plots, and final report
├── requirements.txt         # Python package dependencies
└── readme.md                # This file
```

## 4. File Descriptions

*   **`database/bplustree.py`**: Contains the `BPlusTreeNode` and `BPlusTree` classes. Implements the core B+ Tree logic including insertion with node splitting, deletion with borrowing/merging, search, range queries, and visualization using Graphviz. Handles the low-level data structure management.

*   **`database/table.py`**: Defines the `Table` class. Each `Table` instance represents a logical table with a defined schema. It uses an instance of `BPlusTree` (`self.data`) to store and index records based on a specified `search_key`. It provides methods (`insert`, `get`, `update`, `delete`, `range_query`) that translate table operations into B+ Tree operations. Also includes schema validation.

*   **`database/db_manager.py`**: Defines the `DatabaseManager` class. This acts as the top-level interface, managing multiple "databases" (collections of tables). It handles creating/deleting databases and tables, retrieving specific `Table` objects, and implements the persistence layer (`save_to_disk`, `load_from_disk`) using `pickle` to save/load the entire database state.

*   **`database/performance.py`**: Contains the `PerformanceAnalyzer` class used for benchmarking. It includes methods to generate test data, run timed tests for various operations (insertion, search, etc.) on both B+ Tree and Brute Force structures, and specifically measures peak insertion memory using `tracemalloc`. It compares different B+ Tree insertion strategies (sorted vs. unsorted) and different B+ Tree orders.

*   **`database/bruteforce.py`**: Provides the `BruteForceDB` class, a simple Python list-based implementation used as a baseline for performance comparisons against the B+ Tree. Operations typically have O(N) complexity.

*   **`database/__init__.py`**: An empty file that signifies to Python that the `database` directory should be treated as a package, allowing relative imports within the package (e.g., `from .bplustree import BPlusTree`).

## 5. Operational Flow

This section outlines the typical function call sequence when performing operations, starting from the UI or a script interacting with the `DatabaseManager`.

*(Note: Internal helper functions starting with `_` in `bplustree.py` manage the core tree balancing logic.)*

---

### 5.1 Record Operations (via `Table` object)

*(Assumes `db_manager` instance exists and `table_obj = db_manager.get_table(db_name, table_name)` has been called)*

*   **Insert Record:**
    1.  **`app.py` / Script:** User provides record data (dictionary). Call `table_obj.insert(record_dict)`.
    2.  **`table.py` (`Table.insert`):**
        *   Calls `_validate_record(record_dict)` to check schema compliance.
        *   Extracts the `search_key` value from `record_dict`.
        *   Calls `self.data.search(key)` (where `self.data` is the `BPlusTree` instance) to check for duplicates.
        *   Calls `self.data.insert(key, record_dict)` to insert the key and the *entire record dictionary* into the B+ Tree.
    3.  **`bplustree.py` (`BPlusTree.insert`):**
        *   Calls `_find_leaf(key)` to locate the target leaf node.
        *   Inserts the `key` and `record_dict` (as value) into the leaf node's sorted lists.
        *   Checks if leaf node is full (`len(keys) == order`).
        *   If full, calls `_split_node(leaf)`.
            *   **`_split_node`:** Divides keys/values, creates sibling, links leaves, identifies key to promote/copy.
            *   Calls `_insert_in_parent(original_node, key_to_parent, new_sibling)`.
                *   **`_insert_in_parent`:** Inserts key/pointer into parent. If parent overflows, *recursively calls `_split_node(parent)`*. Handles new root creation if needed.

*   **Search/Get Record (by Key):**
    1.  **`app.py` / Script:** User provides `record_id`. Call `table_obj.get(record_id)`.
    2.  **`table.py` (`Table.get`):**
        *   Calls `self.data.search(record_id)`.
    3.  **`bplustree.py` (`BPlusTree.search`):**
        *   Calls `_find_leaf(record_id)` to locate the target leaf.
        *   Searches within the leaf's `keys` list (using `bisect_left` and check) for the `record_id`.
        *   If found, returns the associated value (the full record dictionary).

*   **Update Record:**
    1.  **`app.py` / Script:** User provides `record_id` and `new_record_data`. Call `table_obj.update(record_id, new_record_data)`.
    2.  **`table.py` (`Table.update`):**
        *   Calls `self.get(record_id)` to check if record exists.
        *   Calls `_validate_record(new_record_data)`.
        *   Checks if `search_key` in `new_record_data` matches `record_id`.
        *   Calls `self.data.update(record_id, new_record_data)`.
    3.  **`bplustree.py` (`BPlusTree.update`):**
        *   Calls `_find_leaf(record_id)` to locate the target leaf.
        *   Finds the index of the `record_id` (using `bisect_left` and check).
        *   If found, replaces the value at that index in the leaf's `values` list with `new_record_data`.

*   **Delete Record (by Key):**
    1.  **`app.py` / Script:** User provides `record_id`. Call `table_obj.delete(record_id)`.
    2.  **`table.py` (`Table.delete`):**
        *   Calls `self.data.delete(record_id)`.
    3.  **`bplustree.py` (`BPlusTree.delete`):**
        *   Calls `_find_leaf(record_id)` to locate the target leaf.
        *   Finds and removes the `key` and `value` from the leaf node's lists.
        *   Checks if leaf node `is_underflow(self._min_keys)`.
        *   If underflow, calls `_handle_underflow(leaf)`.
            *   **`_handle_underflow`:** Checks siblings' capacity (`has_excess_keys`).
            *   If possible, calls `_borrow_from_left` or `_borrow_from_right`.
                *   **`_borrow_...`:** Moves key/value/pointer from sibling through parent; updates parent key.
            *   If borrowing impossible, calls `_merge_nodes`.
                *   **`_merge_nodes`:** Combines nodes, removes key/pointer from parent, updates leaf links. If parent underflows, *recursively calls `_handle_underflow(parent)`*. Handles root height reduction if necessary.

*   **Range Query:**
    1.  **`app.py` / Script:** User provides `start_key`, `end_key`. Call `table_obj.range_query(start_key, end_key)`.
    2.  **`table.py` (`Table.range_query`):**
        *   Calls `self.data.range_query(start_key, end_key)`.
    3.  **`bplustree.py` (`BPlusTree.range_query`):**
        *   Calls `_find_leaf(start_key)` to find the starting leaf.
        *   Iterates through keys/values in the current leaf, adding matches to results.
        *   Follows `next_leaf` pointers to subsequent leaves.
        *   Continues scanning leaves until keys exceed `end_key`.

---

### 5.2 Table & Database Management Operations

*(Assumes `db_manager` instance exists)*

*   **Create Table:**
    1.  **`app.py` / Script:** User provides DB name, table name, schema, etc. Call `db_manager.create_table(...)`.
    2.  **`db_manager.py` (`DatabaseManager.create_table`):**
        *   Checks if DB exists and table name is valid/unique within the DB.
        *   Instantiates `Table(name, schema, order, search_key)`.
            *   **`table.py` (`Table.__init__`):** Validates schema/search key, creates `BPlusTree(order)`.
        *   Stores the new `Table` instance in `self.databases[db_name][table_name]`.

*   **Delete Table:**
    1.  **`app.py` / Script:** User provides DB name, table name. Call `db_manager.delete_table(...)`.
    2.  **`db_manager.py` (`DatabaseManager.delete_table`):**
        *   Checks if DB and table exist.
        *   Uses `del self.databases[db_name][table_name]` to remove the reference. The `Table` object (and its contained `BPlusTree`) will be garbage collected if no other references exist.

*   **Create Database:**
    1.  **`app.py` / Script:** User provides DB name. Call `db_manager.create_database(...)`.
    2.  **`db_manager.py` (`DatabaseManager.create_database`):**
        *   Checks if name is valid/unique.
        *   Adds `db_name: {}` to the `self.databases` dictionary.

*   **Delete Database:**
    1.  **`app.py` / Script:** User provides DB name. Call `db_manager.delete_database(...)`.
    2.  **`db_manager.py` (`DatabaseManager.delete_database`):**
        *   Checks if DB exists.
        *   Uses `del self.databases[db_name]` to remove the entry. All contained `Table` objects will be garbage collected.

*   **Save/Load Database (Persistence):**
    1.  **`app.py` / Script:** User provides file path. Call `db_manager.save_to_disk(filepath)` or `db_manager.load_from_disk(filepath)`.
    2.  **`db_manager.py` (`save_to_disk`/`load_from_disk`):**
        *   Uses the `pickle` library (`pickle.dump`/`pickle.load`) to serialize/deserialize the entire `self.databases` dictionary (including all nested `Table` and `BPlusTree` objects and their states) to/from the specified file.

---
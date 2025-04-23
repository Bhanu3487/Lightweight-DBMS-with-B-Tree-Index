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

db_management_system/
├── database/ # Core database logic
│ ├── init.py # Makes 'database' a Python package
│ ├── **bplustree.py** # B+ Tree implementation (Nodes, Tree logic)
│ ├── table.py # Table class (uses B+ Tree for index)
│ ├── db_manager.py # Manages Databases and Tables, Persistence
│ ├── bruteforce.py # Simple list-based DB for comparison
│ └── performance.py # Performance analysis and benchmarking class
├── saved_data/ # Default directory for saved database state
│ └── *.pkl # Saved database files
├── .gitignore # Specifies intentionally untracked files for Git
├── **app.py** # Streamlit UI application script
├── **report.ipynb** # Jupyter Notebook for analysis, plots, and final report
├── requirements.txt # Python package dependencies
└── readme.md # This file

## 4. File Descriptions

*   **`database/bplustree.py`**: Contains the `BPlusTreeNode` and `BPlusTree` classes. Implements the core B+ Tree logic including insertion with node splitting, deletion with borrowing/merging, search, range queries, and visualization using Graphviz. Handles the low-level data structure management.

*   **`database/table.py`**: Defines the `Table` class. Each `Table` instance represents a logical table with a defined schema. It uses an instance of `BPlusTree` (`self.data`) to store and index records based on a specified `search_key`. It provides methods (`insert`, `get`, `update`, `delete`, `range_query`) that translate table operations into B+ Tree operations. Also includes schema validation.

*   **`database/db_manager.py`**: Defines the `DatabaseManager` class. This acts as the top-level interface, managing multiple "databases" (collections of tables). It handles creating/deleting databases and tables, retrieving specific `Table` objects, and implements the persistence layer (`save_to_disk`, `load_from_disk`) using `pickle` to save/load the entire database state.

*   **`database/performance.py`**: Contains the `PerformanceAnalyzer` class used for benchmarking. It includes methods to generate test data, run timed tests for various operations (insertion, search, etc.) on both B+ Tree and Brute Force structures, and specifically measures peak insertion memory using `tracemalloc`. It compares different B+ Tree insertion strategies (sorted vs. unsorted) and different B+ Tree orders.

*   **`database/bruteforce.py`**: Provides the `BruteForceDB` class, a simple Python list-based implementation used as a baseline for performance comparisons against the B+ Tree. Operations typically have O(N) complexity.

*   **`database/__init__.py`**: An empty file that signifies to Python that the `database` directory should be treated as a package, allowing relative imports within the package (e.g., `from .bplustree import BPlusTree`).


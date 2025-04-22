#app.py
import streamlit as st
import pandas as pd
import sys
import os
import io  # To handle SVG rendering potential issues
import math # Import math if used in BPlusTree or other modules

# --- Add project root to Python path ---
# This allows importing from the 'database' package
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(current_dir) # Assumes app.py is in project root
if project_root not in sys.path:
    sys.path.append(project_root)
# -----------------------------------------

try:
    from database.db_manager import DatabaseManager
    from database.table import Table # For type checking if needed
    from database.bplustree import BPlusTree # For type checking if needed
    import graphviz # To check for executable errors
except ModuleNotFoundError as e:
    st.error(f"Error importing database modules: {e}")
    st.error("Ensure 'app.py' is in the project root directory and the 'database' package exists with '__init__.py'.")
    st.stop() # Stop execution if core modules can't be imported

# --- Helper Functions ---

def parse_schema(schema_str: str) -> dict:
    """Parses a schema string 'col1:type1, col2:type2' into a dict."""
    schema = {}
    type_map = {"int": int, "str": str, "float": float, "bool": bool}
    try:
        parts = schema_str.split(',')
        for part in parts:
            col_name, type_name = part.strip().split(':')
            col_name = col_name.strip()
            type_name = type_name.strip().lower()
            if type_name not in type_map:
                raise ValueError(f"Unsupported type '{type_name}' for column '{col_name}'. Use int, str, float, or bool.")
            schema[col_name] = type_map[type_name]
        if not schema:
             raise ValueError("Schema cannot be empty.")
        return schema
    except Exception as e:
        st.error(f"Invalid schema format. Use 'col1:type1, col2:type2'. Error: {e}")
        return None # Return None on error

def get_widget_value(widget_func, label, schema_type, default=None):
    """Gets value from appropriate streamlit widget based on type."""
    if schema_type == int:
        return widget_func(label, value=default if isinstance(default, int) else 0, step=1)
    elif schema_type == float:
        return widget_func(label, value=default if isinstance(default, float) else 0.0, step=0.1)
    elif schema_type == bool:
        # Represent bool as selectbox for clarity, handling None storage issue
        options = [True, False]
        default_index = options.index(default) if default in options else 0
        return widget_func(label, options=options, index=default_index)
    else: # Default to string
        return widget_func(label, value=default if isinstance(default, str) else "")


# --- Initialize Session State ---
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
    print("Initialized DB Manager in session state.") # For debugging server logs

if 'selected_db' not in st.session_state:
    st.session_state.selected_db = None

if 'selected_table' not in st.session_state:
    st.session_state.selected_table = None

db_manager = st.session_state.db_manager

# --- Constants ---
SAVE_DIR = "saved_data"
DEFAULT_SAVE_FILE = os.path.join(SAVE_DIR, "sports_db.pkl")

# ==================================
# --- Sidebar - DB/Table Management ---
# ==================================
st.sidebar.header("Database Management")

# --- DB Operations ---
db_names, _ = db_manager.list_databases()
st.session_state.selected_db = st.sidebar.selectbox(
    "Select Database", db_names, index=db_names.index(st.session_state.selected_db) if st.session_state.selected_db in db_names else 0, key="db_select"
)

col1, col2 = st.sidebar.columns(2)
with col1:
    new_db_name = st.text_input("New DB Name", key="new_db_name_input")
    if st.button("Create DB", key="create_db_btn"):
        if new_db_name:
            msg, success = db_manager.create_database(new_db_name)
            if success: st.sidebar.success(f"DB '{new_db_name}' created.") ; st.rerun()
            else: st.sidebar.error(msg)
        else:
            st.sidebar.warning("Enter a database name.")

with col2:
    if st.session_state.selected_db:
        if st.button(f"Delete '{st.session_state.selected_db}'", key="delete_db_btn"):
            if st.sidebar.checkbox(f"Confirm deletion of {st.session_state.selected_db}?", key="confirm_del_db"):
                msg, success = db_manager.delete_database(st.session_state.selected_db)
                if success:
                    st.sidebar.success(f"DB '{st.session_state.selected_db}' deleted.")
                    st.session_state.selected_db = None # Reset selection
                    st.session_state.selected_table = None
                    st.rerun() # Reload to update selectbox
                else: st.sidebar.error(msg)

st.sidebar.divider()

# --- Table Operations (only if DB selected) ---
if st.session_state.selected_db:
    st.sidebar.subheader(f"Tables in '{st.session_state.selected_db}'")
    table_names, success = db_manager.list_tables(st.session_state.selected_db)
    if not success: table_names = [] # Handle case where DB might disappear unexpectedly

    st.session_state.selected_table = st.sidebar.selectbox(
        "Select Table", table_names, index=table_names.index(st.session_state.selected_table) if st.session_state.selected_table in table_names else 0, key="table_select"
    )

    with st.sidebar.expander("Create New Table"):
        new_table_name = st.text_input("New Table Name", key="new_table_name_input")
        # Use text area for schema, more user-friendly than complex forms
        schema_str = st.text_area("Schema (e.g., id:int, name:str, active:bool)", "id:int, name:str", key="schema_input")
        search_key_col = st.text_input("Search Key Column Name (from Schema)", "id", key="search_key_input")
        btree_order = st.number_input("B+ Tree Order", min_value=3, value=5, step=1, key="order_input")

        if st.button("Create Table", key="create_table_btn"):
            if new_table_name and schema_str and search_key_col:
                schema = parse_schema(schema_str)
                if schema:
                    if search_key_col not in schema:
                        st.error(f"Search key '{search_key_col}' not found in provided schema keys: {list(schema.keys())}")
                    else:
                         msg, success = db_manager.create_table(
                             st.session_state.selected_db,
                             new_table_name,
                             schema,
                             order=btree_order,
                             search_key=search_key_col
                         )
                         if success: st.success(f"Table '{new_table_name}' created."); st.rerun()
                         else: st.error(msg)
            else:
                st.warning("Please fill in all fields for the new table.")

    if st.session_state.selected_table:
         if st.sidebar.button(f"Delete '{st.session_state.selected_table}' Table", key="delete_table_btn"):
              if st.sidebar.checkbox(f"Confirm deletion of {st.session_state.selected_table}?", key="confirm_del_tbl"):
                    msg, success = db_manager.delete_table(st.session_state.selected_db, st.session_state.selected_table)
                    if success:
                        st.sidebar.success(f"Table '{st.session_state.selected_table}' deleted.")
                        st.session_state.selected_table = None # Reset selection
                        st.rerun() # Reload to update selectbox
                    else: st.sidebar.error(msg)
else:
    st.sidebar.info("Select or create a database to manage tables.")

st.sidebar.divider()

# --- Persistence ---
st.sidebar.subheader("Persistence")
save_load_path = st.sidebar.text_input("Save/Load File Path", value=DEFAULT_SAVE_FILE, key="save_path_input")
col3, col4 = st.sidebar.columns(2)
with col3:
    if st.button("Save State", key="save_db_btn"):
        msg, success = db_manager.save_to_disk(save_load_path)
        if success: st.sidebar.success("DB state saved.")
        else: st.sidebar.error(msg)
with col4:
     if st.button("Load State", key="load_db_btn"):
         msg, success = db_manager.load_from_disk(save_load_path)
         if success:
             st.sidebar.success("DB state loaded.")
             # Reset selections as loaded state might not have them
             st.session_state.selected_db = None
             st.session_state.selected_table = None
             st.rerun() # Force rerun to update UI with loaded state
         else: st.sidebar.error(msg)


# ============================
# --- Main Area - Operations ---
# ============================
st.title("B+ Tree DBMS Interface")

if not st.session_state.selected_db:
    st.info("⬅️ Select or Create a Database in the sidebar to begin.")
elif not st.session_state.selected_table:
    st.info(f"⬅️ Select or Create a Table within the '{st.session_state.selected_db}' database in the sidebar.")
else:
    # Get selected table object
    current_table, success = db_manager.get_table(st.session_state.selected_db, st.session_state.selected_table)

    if not success or not current_table:
        st.error(f"Could not load table '{st.session_state.selected_table}'. It might have been deleted.")
        st.session_state.selected_table = None # Reset selection
        st.stop()

    st.header(f"Table: `{current_table.name}`")
    st.caption(f"Database: `{st.session_state.selected_db}` | B+Tree Order: `{current_table.order}` | Search Key: `{current_table.search_key}`")
    st.json(current_table.schema, expanded=False) # Show schema collapsed

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Insert", "Get Record", "Get All", "Range Query", "Delete", "Visualize Tree"])

    # --- Insert Tab ---
    with tab1:
        st.subheader("Insert New Record")
        with st.form("insert_form"):
            record_input = {}
            for col_name, col_type in current_table.schema.items():
                # Use helper to create appropriate widget
                record_input[col_name] = get_widget_value(st.text_input if col_type==str else st.number_input if col_type in [int, float] else st.selectbox, f"{col_name} ({col_type.__name__})", col_type)

            submitted = st.form_submit_button("Insert Record")
            if submitted:
                # Convert bool from selectbox if needed
                for col_name, col_type in current_table.schema.items():
                    if col_type == bool:
                        # Ensure value is actual boolean
                        record_input[col_name] = bool(record_input[col_name])

                # Attempt insertion
                success, msg = current_table.insert(record_input)
                if success:
                    st.success("Record inserted successfully!")
                else:
                    st.error(f"Insertion Failed: {msg}")

    # --- Get Record Tab ---
    with tab2:
        st.subheader("Get Record by ID")
        search_key_type = current_table.schema.get(current_table.search_key, str) # Default to str if somehow missing
        with st.form("get_form"):
             record_id_str = st.text_input(f"Enter {current_table.search_key} (ID)")
             submitted = st.form_submit_button("Get Record")
             if submitted:
                 if not record_id_str:
                     st.warning("Please enter a Record ID.")
                 else:
                    try:
                        # Try converting ID to the expected type
                        record_id = search_key_type(record_id_str)
                        record, found = current_table.get(record_id)
                        if found:
                            st.success(f"Record found for ID {record_id}:")
                            st.json(record)
                        else:
                            st.warning(f"Record not found for ID {record_id}.")
                    except ValueError:
                        st.error(f"Invalid ID format. Expected type: {search_key_type.__name__}")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

    # --- Get All Tab ---
    with tab3:
        st.subheader("Get All Records")
        if st.button("Load All Records", key="get_all_btn"):
            all_records, success = current_table.get_all()
            if success:
                st.write(f"Found {len(all_records)} records:")
                # Use Pandas DataFrame for nice table display
                if all_records:
                     df = pd.DataFrame(all_records)
                     st.dataframe(df)
                else:
                     st.info("Table is empty.")
            else:
                 st.error("Failed to retrieve all records.")


    # --- Range Query Tab ---
    with tab4:
        st.subheader("Range Query")
        search_key_type = current_table.schema.get(current_table.search_key, str)
        with st.form("range_form"):
            col_range1, col_range2 = st.columns(2)
            with col_range1:
                 start_key_str = st.text_input(f"Start {current_table.search_key}")
            with col_range2:
                 end_key_str = st.text_input(f"End {current_table.search_key}")

            submitted = st.form_submit_button("Run Range Query")
            if submitted:
                if not start_key_str or not end_key_str:
                    st.warning("Please enter both Start and End keys.")
                else:
                    try:
                         start_key = search_key_type(start_key_str)
                         end_key = search_key_type(end_key_str)
                         if start_key > end_key:
                              st.warning("Start key cannot be greater than End key.")
                         else:
                              results, success = current_table.range_query(start_key, end_key)
                              if success:
                                   st.write(f"Found {len(results)} records in range [{start_key} - {end_key}]:")
                                   if results:
                                        df = pd.DataFrame(results)
                                        st.dataframe(df)
                                   else:
                                        st.info("No records found in this range.")
                              else:
                                   st.error("Range query failed.")
                    except ValueError:
                        st.error(f"Invalid key format. Expected type: {search_key_type.__name__}")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

    # --- Delete Tab ---
    with tab5:
         st.subheader("Delete Record by ID")
         search_key_type = current_table.schema.get(current_table.search_key, str)
         with st.form("delete_form"):
             record_id_del_str = st.text_input(f"Enter {current_table.search_key} (ID) to Delete")
             submitted = st.form_submit_button("Delete Record")
             if submitted:
                 if not record_id_del_str:
                     st.warning("Please enter a Record ID.")
                 else:
                     try:
                         record_id_del = search_key_type(record_id_del_str)
                         # Optional: Add confirmation checkbox inside form
                         # confirm_del = st.checkbox("Confirm Deletion?")
                         # if confirm_del:
                         success, msg = current_table.delete(record_id_del)
                         if success:
                             st.success(f"Record with ID {record_id_del} deleted successfully!")
                         else:
                             st.error(f"Deletion Failed: {msg}")
                         # else: st.warning("Deletion not confirmed.")
                     except ValueError:
                         st.error(f"Invalid ID format. Expected type: {search_key_type.__name__}")
                     except Exception as e:
                         st.error(f"An error occurred: {e}")

    # --- Visualize Tab ---
    with tab6:
        st.subheader("Visualize B+ Tree Index")
        if st.button("Generate Visualization", key="viz_btn"):
             if current_table and isinstance(current_table.data, BPlusTree):
                 st.write("Generating tree... (may take a moment for large trees)")
                 dot = current_table.data.visualize_tree()
                 if dot:
                     try:
                          # Render to SVG and display using st.image
                          # Using BytesIO avoids temporary file creation
                          svg_bytes = dot.pipe(format='svg')
                          st.image(svg_bytes.decode('utf-8'), use_container_width=True)
                     except graphviz.backend.execute.ExecutableNotFound:
                         st.error("Graphviz executable not found in system PATH. Please install Graphviz (https://graphviz.org/download/) and add it to PATH.")
                     except Exception as e:
                         st.error(f"An error occurred during visualization: {e}")
                 else:
                     st.warning("Could not generate visualization object (tree might be empty or error occurred).")
             else:
                 st.error("Cannot visualize. Invalid table data structure.")
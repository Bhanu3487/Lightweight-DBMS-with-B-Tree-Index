# # File: db_management_system/database/bplustree.py
# import bisect
# import math

# class BPlusTreeNode:
#     """Represents a node in the B+ Tree (Internal or Leaf)."""
#     def __init__(self, order, parent=None, is_leaf=False):
#         self.order = order
#         self.parent = parent
#         self.keys = []
#         self.values = [] # Child nodes for Internal, data values for Leaf
#         self.is_leaf = is_leaf
#         self.next_leaf = None # Only for leaf nodes

#     def __repr__(self):
#         # Helper for debugging
#         return f"Node({'L' if self.is_leaf else 'I'}, K:{self.keys})"

#     def is_full(self):
#         """Node has max number of keys (order - 1)."""
#         return len(self.keys) == self.order - 1

#     def can_borrow(self):
#         """Node has more than the minimum number of keys."""
#         min_keys = math.ceil(self.order / 2) - 1
#         return len(self.keys) > min_keys

#     def is_underflow(self):
#         """Node has less than the minimum number of keys."""
#         # Root has special minimum rules (can have 1 key if internal, 0 if leaf)
#         if self.parent is None:
#             return False # Root doesn't underflow in the traditional sense
#         min_keys = math.ceil(self.order / 2) - 1
#         return len(self.keys) < min_keys

#     def find_child_index(self, key):
#         """Finds the index of the child pointer to follow for a given key."""
#         assert not self.is_leaf, "Cannot find child index in a leaf node."
#         # bisect_left returns the index where key should be inserted.
#         # This index directly corresponds to the child pointer index.
#         return bisect.bisect_left(self.keys, key)

# class BPlusTree:
#     """B+ Tree Implementation."""
#     def __init__(self, order=4):
#         if order < 3:
#             raise ValueError("B+ Tree order must be at least 3")
#         self.order = order
#         self.root = BPlusTreeNode(order, is_leaf=True)
#         # Calculate min keys for non-root nodes once
#         self._min_keys = math.ceil(self.order / 2) - 1

#     # --- Core Search ---
#     # def _find_leaf(self, key):
#     #     """Find the leaf node where the key should exist."""
#     #     node = self.root
#     #     while not node.is_leaf:
#     #         # --- Pre-traversal Invariant Check ---
#     #         assert len(node.values) == len(node.keys) + 1, \
#     #             f"Invariant Violation: Node {node} has {len(node.keys)} keys but {len(node.values)} children."

#     #         # idx = node.find_child_index(key)
#     #         idx = bisect.bisect_right(node.keys, key) 

#     #         # --- Pre-traversal Index Check ---
#     #         assert idx < len(node.values), \
#     #             f"Index Calculation Error: idx={idx}, len(values)={len(node.values)} in Node {node}"

#     #         next_node = node.values[idx]

#     #         # --- Pre-traversal Parent Pointer Check ---
#     #         assert next_node.parent is node, \
#     #             f"Parent Pointer Error: Child {next_node} parent is {next_node.parent}, expected {node}"

#     #         node = next_node
#     #     return node
#     # Inside BPlusTree class in db_management_system/database/bplustree.py

#     def _find_leaf(self, key):
#         """Find the leaf node where the key should exist."""
#         node = self.root
#         while not node.is_leaf:
#             # --- Pre-traversal Invariant Check ---
#             assert len(node.values) == len(node.keys) + 1, \
#                 f"Invariant Violation: Node {node} has {len(node.keys)} keys but {len(node.values)} children."

#             # --- Use bisect_right for traversal logic ---
#             idx = bisect.bisect_right(node.keys, key) # <<< CHANGE HERE
#             # idx is now the index of the correct child pointer to follow

#             # --- Pre-traversal Index Check ---
#             assert idx < len(node.values), \
#                 f"Index Calculation Error: idx={idx}, len(values)={len(node.values)} in Node {node} using bisect_right"

#             next_node = node.values[idx]

#             # --- Pre-traversal Parent Pointer Check ---
#             assert next_node.parent is node, \
#                 f"Parent Pointer Error: Child {next_node} parent is {next_node.parent}, expected {node}"

#             node = next_node
#         return node

#     def search(self, key):
#         """Search for a key and return its value, or None."""
#         leaf = self._find_leaf(key)
#         try:
#             idx = leaf.keys.index(key)
#             return leaf.values[idx]
#         except ValueError:
#             return None

#     # --- Insertion ---
#     def insert(self, key, value):
#         """Insert a key-value pair into the tree."""
#         leaf = self._find_leaf(key)

#         # Optional: Handle duplicates (e.g., update or raise error)
#         # if key in leaf.keys:
#         #     self.update(key, value) # Example: Update on duplicate
#         #     return

#         # Insert key and value into sorted leaf node
#         insert_idx = bisect.bisect_left(leaf.keys, key)
#         leaf.keys.insert(insert_idx, key)
#         leaf.values.insert(insert_idx, value)

#         # Handle node overflow (split)
#         if len(leaf.keys) == self.order: # Max keys is order-1, so == order means overflow
#             self._split_node(leaf)

#     def _split_node(self, node):
#         """Splits an overflowing node (leaf or internal)."""
#         mid_idx = self.order // 2 # Split point index

#         # Create new sibling node
#         new_sibling = BPlusTreeNode(self.order, parent=node.parent, is_leaf=node.is_leaf)

#         if node.is_leaf:
#             # --- Leaf Split ---
#             key_to_parent = node.keys[mid_idx] # Copy up first key of new sibling

#             new_sibling.keys = node.keys[mid_idx:]
#             new_sibling.values = node.values[mid_idx:] # Data values
#             node.keys = node.keys[:mid_idx]
#             node.values = node.values[:mid_idx]

#             # Link leaves
#             new_sibling.next_leaf = node.next_leaf
#             node.next_leaf = new_sibling
#         else:
#             # --- Internal Split ---
#             key_to_parent = node.keys[mid_idx] # Promote middle key (removed from children)

#             new_sibling.keys = node.keys[mid_idx + 1:]
#             new_sibling.values = node.values[mid_idx + 1:] # Child pointers
#             node.keys = node.keys[:mid_idx]
#             node.values = node.values[:mid_idx + 1] # Child pointers

#             # Update parent pointers for children moved to new sibling
#             for child in new_sibling.values:
#                 assert child.parent is node, f"Child {child} parent incorrect before update"
#                 child.parent = new_sibling

#             # Assert invariants after internal split
#             assert len(node.values) == len(node.keys) + 1, "Original node invariant broken after internal split"
#             assert len(new_sibling.values) == len(new_sibling.keys) + 1, "New sibling invariant broken after internal split"

#         # Insert key and pointer into parent (handles root splitting)
#         self._insert_in_parent(node, key_to_parent, new_sibling)

#     def _insert_in_parent(self, left_child, key, right_child):
#         """Inserts key and right_child pointer into parent after a split."""
#         parent = left_child.parent

#         if parent is None: # Original node was the root
#             new_root = BPlusTreeNode(self.order, is_leaf=False)
#             new_root.keys = [key]
#             new_root.values = [left_child, right_child]

#             # Update parent pointers of children *before* changing self.root
#             left_child.parent = new_root
#             right_child.parent = new_root
#             self.root = new_root # Update tree root reference
#             return

#         # Parent exists, insert key and child pointer
#         insert_idx = bisect.bisect_left(parent.keys, key)
#         parent.keys.insert(insert_idx, key)
#         parent.values.insert(insert_idx + 1, right_child)
#         right_child.parent = parent # Set parent for the newly added child

#         # Check parent invariant
#         assert len(parent.values) == len(parent.keys) + 1, "Parent invariant broken after insert"

#         # Handle potential parent overflow
#         if len(parent.keys) == self.order:
#             self._split_node(parent)

#     # --- Deletion ---
#     def delete(self, key):
#         """Delete a key-value pair from the tree."""
#         leaf = self._find_leaf(key) # Step 1: Find leaf
#         try:
#             idx = leaf.keys.index(key) # Step 2a: Find key index in leaf
#             leaf.keys.pop(idx)         # Step 2b: Remove key
#             leaf.values.pop(idx)       # Step 2c: Remove value

#             # Handle underflow if necessary
#             if leaf.is_underflow():    # Step 3 & 4
#                 self._handle_underflow(leaf)
#             return True # <<< SUCCESS
#         except ValueError:
#             return False # <<< FAILURE: Key not found in leaf
#         except Exception as e:
#             print(f"!!! Unexpected error during delete for key {key}: {e}") # Added for debug
#             raise # Re-raise unexpected errors

#     def _handle_underflow(self, node):
#         """Handles node underflow by borrowing or merging."""
#         # Root adjustment is handled here
#         if node.parent is None:
#             # If root is internal, non-leaf, has no keys left, and only one child
#             if not node.is_leaf and not node.keys and len(node.values) == 1:
#                 self.root = node.values[0] # Make child the new root
#                 self.root.parent = None
#             # Otherwise (empty leaf root, or internal root with keys), root is fine
#             return

#         parent = node.parent
#         # Find node's index relative to its siblings in the parent
#         try:
#             child_index = parent.values.index(node)
#         except ValueError:
#              raise RuntimeError(f"Consistency Error: Node {node} not found in parent {parent}'s children.")

#         # Try borrowing from left sibling
#         if child_index > 0:
#             left_sibling = parent.values[child_index - 1]
#             if left_sibling.can_borrow():
#                 self._borrow_from_left(node, left_sibling, parent, child_index)
#                 return

#         # Try borrowing from right sibling
#         if child_index < len(parent.values) - 1:
#             right_sibling = parent.values[child_index + 1]
#             if right_sibling.can_borrow():
#                 self._borrow_from_right(node, right_sibling, parent, child_index)
#                 return

#         # If borrowing failed, merge
#         if child_index > 0:
#             # Merge node into left sibling
#             left_sibling = parent.values[child_index - 1]
#             self._merge_nodes(left_sibling, node, parent, child_index - 1)
#         elif child_index < len(parent.values) - 1: # Should only happen if child_index is 0
#              # Merge right sibling into node
#              right_sibling = parent.values[child_index + 1]
#              self._merge_nodes(node, right_sibling, parent, child_index)
#         else:
#             # This case *shouldn't* be reachable if root handling is correct
#             raise RuntimeError("Reached unexpected state in handle_underflow: cannot borrow or merge.")

#     def _borrow_from_left(self, node, left_sibling, parent, node_idx_in_parent):
#         """Borrows an element from the left sibling."""
#         separator_parent_idx = node_idx_in_parent - 1
#         if node.is_leaf:
#             # Move last key/value from left sibling to start of node
#             key_to_move = left_sibling.keys.pop()
#             value_to_move = left_sibling.values.pop()
#             node.keys.insert(0, key_to_move)
#             node.values.insert(0, value_to_move)
#             # Update parent separator key
#             parent.keys[separator_parent_idx] = node.keys[0] # New first key
#         else: # Internal node
#             # Pull separator key down from parent
#             separator_key = parent.keys[separator_parent_idx]
#             node.keys.insert(0, separator_key)
#             # Move last key from left sibling up to parent
#             parent.keys[separator_parent_idx] = left_sibling.keys.pop()
#             # Move last child pointer from left sibling to start of node
#             child_to_move = left_sibling.values.pop()
#             node.values.insert(0, child_to_move)
#             child_to_move.parent = node # Update moved child's parent

#         # Assert invariants
#         assert len(left_sibling.values) == len(left_sibling.keys) + (0 if left_sibling.is_leaf else 1)
#         assert len(node.values) == len(node.keys) + (0 if node.is_leaf else 1)


#     def _borrow_from_right(self, node, right_sibling, parent, node_idx_in_parent):
#         """Borrows an element from the right sibling."""
#         separator_parent_idx = node_idx_in_parent
#         if node.is_leaf:
#             # Move first key/value from right sibling to end of node
#             key_to_move = right_sibling.keys.pop(0)
#             value_to_move = right_sibling.values.pop(0)
#             node.keys.append(key_to_move)
#             node.values.append(value_to_move)
#             # Update parent separator key
#             parent.keys[separator_parent_idx] = right_sibling.keys[0] # New first key of sibling
#         else: # Internal node
#             # Pull separator key down from parent
#             separator_key = parent.keys[separator_parent_idx]
#             node.keys.append(separator_key)
#             # Move first key from right sibling up to parent
#             parent.keys[separator_parent_idx] = right_sibling.keys.pop(0)
#             # Move first child pointer from right sibling to end of node
#             child_to_move = right_sibling.values.pop(0)
#             node.values.append(child_to_move)
#             child_to_move.parent = node # Update moved child's parent

#         # Assert invariants
#         assert len(right_sibling.values) == len(right_sibling.keys) + (0 if right_sibling.is_leaf else 1)
#         assert len(node.values) == len(node.keys) + (0 if node.is_leaf else 1)

#     def _merge_nodes(self, left_node, right_node, parent, left_node_idx_in_parent):
#         """Merges right_node into left_node."""
#         # Remove separator key from parent
#         separator_key = parent.keys.pop(left_node_idx_in_parent)
#         # Remove pointer to right_node from parent
#         parent.values.pop(left_node_idx_in_parent + 1)

#         if not left_node.is_leaf: # Internal node merge
#             # Pull separator key down
#             left_node.keys.append(separator_key)
#             # Append keys and children from right node
#             left_node.keys.extend(right_node.keys)
#             left_node.values.extend(right_node.values)
#             # Update parent pointers of moved children
#             for child in right_node.values:
#                 assert child.parent is right_node
#                 child.parent = left_node
#         else: # Leaf node merge
#             left_node.keys.extend(right_node.keys)
#             left_node.values.extend(right_node.values)
#             # Update linked list pointer
#             left_node.next_leaf = right_node.next_leaf

#         # Assert merged node invariant
#         assert len(left_node.values) == len(left_node.keys) + (0 if left_node.is_leaf else 1)

#         # Discard right_node (garbage collection)

#         # Check if parent underflows after losing key/child
#         if parent.is_underflow():
#             self._handle_underflow(parent)


#     # --- Other Operations ---
#     def update(self, key, new_value):
#         """Update value for an existing key. Returns True/False."""
#         leaf = self._find_leaf(key)
#         try:
#             idx = leaf.keys.index(key)
#             leaf.values[idx] = new_value
#             return True
#         except ValueError:
#             return False

#     def range_query(self, start_key, end_key):
#         """Return key-value pairs within the range [start_key, end_key]."""
#         result = []
#         leaf = self._find_leaf(start_key)
#         while leaf is not None:
#             for i, k in enumerate(leaf.keys):
#                 if k >= start_key:
#                     if k <= end_key:
#                         result.append((k, leaf.values[i]))
#                     else:
#                         # Key exceeds range end, stop searching
#                         return result # Early exit
#             # Move to the next leaf if current key <= end_key
#             if not leaf.keys or leaf.keys[-1] <= end_key:
#                  leaf = leaf.next_leaf
#             else:
#                  break # All remaining keys in this leaf are > end_key

#         return result

#     def get_all(self):
#         """Return all key-value pairs in order."""
#         result = []
#         node = self.root
#         # Find the first leaf node
#         while not node.is_leaf:
#              if not node.values: return [] # Empty tree case
#              node = node.values[0]
#         # Traverse leaf linked list
#         while node is not None:
#             for i, k in enumerate(node.keys):
#                 result.append((k, node.values[i]))
#             node = node.next_leaf
#         return result

#     # --- Visualization (Requires graphviz library and executable) ---
#     def visualize_tree(self):
#         """
#         Generates a Graphviz Digraph object for visualization.
#         Uses HTML-like labels for better edge rendering with record shapes.
#         """
#         try:
#             from graphviz import Digraph
#             # Check if graphviz version supports HTML labels well enough
#             # Not strictly necessary but good practice if version specific features are used
#         except ImportError:
#             print("Install graphviz library and executable for visualization.")
#             return None

#         # Use node_attr shape='plain' so HTML table defines the shape
#         dot = Digraph(comment='B+ Tree', node_attr={'shape': 'plain'})

#         if not self.root or (self.root.is_leaf and not self.root.keys):
#             dot.node('empty', 'Tree is empty')
#             return dot

#         node_queue = [(self.root, 'node_root')]
#         node_id_map = {self.root: 'node_root'}
#         id_counter = 0
#         processed_nodes = set()
#         all_leaf_render_info = []

#         while node_queue:
#             current_node, node_id = node_queue.pop(0)
#             if current_node in processed_nodes: continue
#             processed_nodes.add(current_node)

#             html_label = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
#             if not current_node.is_leaf: # Internal Node (Revised HTML v2)
#                 html_label = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
#                 # Row 1: Pointers
#                 html_label += '<TR>'
#                 for i in range(len(current_node.values)):
#                     html_label += f'<TD PORT="f{i}">P{i}</TD>'
#                 html_label += '</TR>'
#                 # Row 2: Keys (Aligned under the gaps)
#                 html_label += '<TR>'
#                 # Add a leading empty cell for alignment before the first key
#                 html_label += '<TD></TD>'
#                 # Add each key, followed by an empty cell spacer
#                 for i, key in enumerate(current_node.keys):
#                     # COLSPAN=1 makes it explicit, though it's default
#                     html_label += f'<TD COLSPAN="1">{key}</TD>'
#                     html_label += f'<TD COLSPAN="1"></TD>' 
                    
#                 # --- Let's try the COLSPAN approach for alignment ---
#                 # This aims to have the key span the space between two pointer ports visually
#                 html_label = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">' # Removed cellpadding for simplicity now
#                 html_label += '<TR>'
#                 # Create a cell for each pointer/port
#                 for i in range(len(current_node.values)):
#                      html_label += f'<TD PORT="f{i}">P{i}</TD>'
#                 html_label += '</TR>'
#                 # Create a second row for keys, using COLSPAN=2 to align keys between pointers
#                 html_label += '<TR>'
#                 html_label += '<TD></TD>' # Add an empty cell before the first key slot
#                 for i, key in enumerate(current_node.keys):
#                     # Each key visually spans the gap between P_i and P_{i+1}
#                     html_label += f'<TD COLSPAN="1">{key}</TD>' # Let key take one column
#                     # Add spacer? Maybe not needed if COLSPAN works well.
#                     html_label += '<TD></TD>' # Add spacer after key
#                 # Pad if necessary? Let's omit complex padding for now.
#                 # We need total number of cells to match pointer row *if* we weren't using colspan
#                 # With colspan, structure is different. Let's try the simple key structure again.

#                 # --- FINAL ATTEMPT: SIMPLEST HTML INTERNAL NODE ---
#                 html_label = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
#                 # Row 1: Keys centered in cells spanning 2 underlying "columns"
#                 html_label += '<TR>'
#                 for i, key in enumerate(current_node.keys):
#                     html_label += f'<TD COLSPAN="2">{key}</TD>'
#                 # Add empty cell if needed to balance columns? If #keys < #pointers-1
#                 if len(current_node.keys) < len(current_node.values) -1 :
#                      html_label += '<TD COLSPAN="2"></TD>' * (len(current_node.values) - 1 - len(current_node.keys))
#                 html_label += '</TR>'
#                  # Row 2: Pointers in cells spanning 2 underlying "columns"
#                 html_label += '<TR>'
#                 for i in range(len(current_node.values)):
#                     html_label += f'<TD PORT="f{i}" COLSPAN="2">P{i}</TD>' # Ports still needed
#                 html_label += '</TR>'


#                 html_label += '</TABLE>>'
#                 dot.node(node_id, label=html_label)

#                 # Add Children/Edges
#                 for i, child in enumerate(current_node.values):
#                     if child not in node_id_map:
#                          id_counter += 1; child_id = f"node_{id_counter}"; node_id_map[child] = child_id
#                     else: child_id = node_id_map[child]
#                     if child not in processed_nodes and child not in [n for n, id_str in node_queue]: node_queue.append((child, child_id))
#                     # Connect edge TO the port in the pointer row (f{i})
#                     dot.edge(f"{node_id}:f{i}", child_id) # Targeting port f{i}

#             else: # Leaf Node (Keep existing working HTML label)
#                 if not current_node.keys:
#                      html_label = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"><TR><TD BGCOLOR="lightblue">Empty Leaf</TD></TR></TABLE>>'
#                 else:
#                     label_keys = '<TR>' + ''.join([f'<TD PORT="k{i}" BGCOLOR="lightblue">{key}</TD>' for i, key in enumerate(current_node.keys)]) + '</TR>'
#                     label_vals = '<TR>' + ''.join([f'<TD PORT="v{i}" BGCOLOR="lightblue">V({current_node.keys[i]})</TD>' for i in range(len(current_node.keys))]) + '</TR>' # Assume values len == keys len
#                     html_label = f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">{label_keys}{label_vals}</TABLE>>'
#                 dot.node(node_id, label=html_label)
#                 all_leaf_render_info.append((current_node, node_id))
#             # --- End Label Generation ---

#         # --- Draw Leaf Links (using node center points, potentially more stable) ---
#         first_leaf = self.root
#         while first_leaf and not first_leaf.is_leaf:
#              if not first_leaf.values: break
#              first_leaf = first_leaf.values[0]

#         obj_to_id = {node_obj: node_str_id for node_obj, node_str_id in all_leaf_render_info}

#         visited_leaves = set()
#         current_leaf_obj = first_leaf
#         while current_leaf_obj and current_leaf_obj not in visited_leaves:
#             visited_leaves.add(current_leaf_obj)
#             current_leaf_id = obj_to_id.get(current_leaf_obj)
#             next_leaf_obj = current_leaf_obj.next_leaf
#             next_leaf_id = obj_to_id.get(next_leaf_obj)

#             if current_leaf_id and next_leaf_id:
#                  # Connect center of nodes for leaf links when using HTML tables
#                  dot.edge(f"{current_leaf_id}", f"{next_leaf_id}", style='dashed', arrowhead='none', constraint='false')

#             current_leaf_obj = next_leaf_obj
#         # --- End Leaf Links ---

#         return dot
    
# File: db_management_system/database/bplustree.py
import bisect
import math
from typing import Any, List, Optional, Tuple, Union # Added for type hinting

# Type Alias for Node Values
NodeValue = Union['BPlusTreeNode', Any] # Can be a child node or actual data

class BPlusTreeNode:
    """Represents a node in the B+ Tree (Internal or Leaf)."""
    def __init__(self, order: int, parent: Optional['BPlusTreeNode'] = None, is_leaf: bool = False):
        self.order: int = order
        self.parent: Optional[BPlusTreeNode] = parent
        self.keys: List[Any] = []
        self.values: List[NodeValue] = [] # Child nodes for Internal, data values for Leaf
        self.is_leaf: bool = is_leaf
        self.next_leaf: Optional[BPlusTreeNode] = None # Only for leaf nodes

    def __repr__(self) -> str:
        # Helper for debugging
        key_str = ", ".join(map(str, self.keys))
        return f"Node({'L' if self.is_leaf else 'I'}, K:[{key_str}])"

    def is_full(self) -> bool:
        """Node has max number of keys (order - 1)."""
        return len(self.keys) == self.order - 1

    # Renamed for clarity and uses pre-calculated min_keys from tree instance
    def has_excess_keys(self, min_keys: int) -> bool:
        """Node has more than the minimum number of keys."""
        return len(self.keys) > min_keys

    # Uses pre-calculated min_keys from tree instance
    def is_underflow(self, min_keys: int) -> bool:
        """Node has less than the minimum number of keys."""
        # Root has special minimum rules (can have 1 key if internal, 0 if leaf)
        if self.parent is None:
            return False # Root doesn't underflow in the traditional sense
        return len(self.keys) < min_keys

    # Removed find_child_index, using bisect directly in _find_leaf


class BPlusTree:
    """B+ Tree Implementation."""
    def __init__(self, order: int = 4):
        if order < 3:
            raise ValueError("B+ Tree order must be at least 3")
        self.order: int = order
        self.root: BPlusTreeNode = BPlusTreeNode(order, is_leaf=True)
        # Calculate min keys for non-root nodes once and store it
        self._min_keys: int = math.ceil(self.order / 2) - 1

    # --- Core Traversal ---
    def _find_leaf(self, key: Any) -> BPlusTreeNode:
        """Find the leaf node where the key should exist."""
        node = self.root
        while not node.is_leaf:
            # --- Pre-traversal Invariant Check ---
            assert len(node.values) == len(node.keys) + 1, \
                f"Invariant Violation: Node {node} has {len(node.keys)} keys but {len(node.values)} children."

            # --- Use bisect_right for traversal logic ---
            idx = bisect.bisect_right(node.keys, key)

            # --- Pre-traversal Index Check ---
            assert idx < len(node.values), \
                f"Index Calculation Error: idx={idx}, len(values)={len(node.values)} in Node {node} using bisect_right"

            next_node = node.values[idx]

            # --- Pre-traversal Parent Pointer Check ---
            assert next_node.parent is node, \
                f"Parent Pointer Error: Child {next_node} parent is {next_node.parent}, expected {node}"

            node = next_node # type: ignore # Ignore type checker warning here, it must be a node
        return node # Type checker knows this is a BPlusTreeNode (specifically, a leaf)

    # --- Public Operations ---

    def search(self, key: Any) -> Optional[Any]:
        """Search for a key and return its value, or None."""
        leaf = self._find_leaf(key)
        try:
            # Use bisect_left to find potential index efficiently
            idx = bisect.bisect_left(leaf.keys, key)
            # Verify if the key at that index actually matches
            if idx < len(leaf.keys) and leaf.keys[idx] == key:
                return leaf.values[idx]
            else:
                return None
        except IndexError: # Should not happen if bisect logic is correct
             return None

    def insert(self, key: Any, value: Any) -> None:
        """Insert a key-value pair into the tree."""
        leaf = self._find_leaf(key)

        # Check for duplicates before inserting (optional, depends on requirements)
        # idx_found = bisect.bisect_left(leaf.keys, key)
        # if idx_found < len(leaf.keys) and leaf.keys[idx_found] == key:
        #     # Handle duplicate: Option 1: Update value
        #     # leaf.values[idx_found] = value
        #     # return
        #     # Handle duplicate: Option 2: Raise error
        #     # raise ValueError(f"Duplicate key {key} found.")
        #     # Handle duplicate: Option 3: Ignore (do nothing - current behavior without check)
        #     pass

        # Insert key and value into sorted leaf node using bisect_left index
        insert_idx = bisect.bisect_left(leaf.keys, key)
        leaf.keys.insert(insert_idx, key)
        leaf.values.insert(insert_idx, value)

        # Handle node overflow (split)
        # Max keys is order-1. If len == order, it has overflowed.
        if len(leaf.keys) == self.order:
            self._split_node(leaf)

    def delete(self, key: Any) -> bool:
        """Delete a key-value pair from the tree. Returns True if successful."""
        leaf = self._find_leaf(key)
        try:
            # Find the exact index of the key
            idx = leaf.keys.index(key) # Direct check if key exists
            leaf.keys.pop(idx)
            leaf.values.pop(idx)

            # Handle underflow if necessary using the stored _min_keys
            if leaf.is_underflow(self._min_keys):
                self._handle_underflow(leaf)
            return True # SUCCESS
        except ValueError:
            return False # FAILURE: Key not found in leaf
        except Exception as e:
            print(f"!!! Unexpected error during delete for key {key}: {e}")
            raise # Re-raise unexpected errors

    def update(self, key: Any, new_value: Any) -> bool:
        """Update value for an existing key. Returns True/False."""
        leaf = self._find_leaf(key)
        try:
            idx = bisect.bisect_left(leaf.keys, key)
            if idx < len(leaf.keys) and leaf.keys[idx] == key:
                 leaf.values[idx] = new_value
                 return True
            else:
                 return False # Key not found at expected index
        except IndexError:
            return False

    def range_query(self, start_key: Any, end_key: Any) -> List[Tuple[Any, Any]]:
        """Return key-value pairs within the range [start_key, end_key]."""
        result: List[Tuple[Any, Any]] = []
        leaf = self._find_leaf(start_key)

        while leaf is not None:
            # Iterate through keys/values in the current leaf
            for i, k in enumerate(leaf.keys):
                if k >= start_key:
                    if k <= end_key:
                        result.append((k, leaf.values[i]))
                    else:
                        # Key exceeds range end, stop searching entirely
                        return result # Early exit
            # Stop if this leaf node has no keys or its last key is already beyond end_key
            if not leaf.keys or leaf.keys[-1] >= end_key:
                 break
            # Move to the next leaf
            leaf = leaf.next_leaf

        return result

    def get_all(self) -> List[Tuple[Any, Any]]:
        """Return all key-value pairs in order."""
        result: List[Tuple[Any, Any]] = []
        node = self.root
        # Find the first leaf node
        while not node.is_leaf:
             if not node.values: return [] # Empty internal node check
             node = node.values[0] # type: ignore
        # Traverse leaf linked list
        current_leaf: Optional[BPlusTreeNode] = node
        while current_leaf is not None:
            for i, k in enumerate(current_leaf.keys):
                result.append((k, current_leaf.values[i]))
            current_leaf = current_leaf.next_leaf
        return result

    # --- Internal Helper Methods ---

    def _split_node(self, node: BPlusTreeNode) -> None:
        """Splits an overflowing node (leaf or internal)."""
        mid_idx = self.order // 2
        new_sibling = BPlusTreeNode(self.order, parent=node.parent, is_leaf=node.is_leaf)

        if node.is_leaf:
            key_to_parent = node.keys[mid_idx]
            new_sibling.keys = node.keys[mid_idx:]
            new_sibling.values = node.values[mid_idx:]
            node.keys = node.keys[:mid_idx]
            node.values = node.values[:mid_idx]
            new_sibling.next_leaf = node.next_leaf
            node.next_leaf = new_sibling
        else: # Internal node
            key_to_parent = node.keys[mid_idx]
            new_sibling.keys = node.keys[mid_idx + 1:]
            new_sibling.values = node.values[mid_idx + 1:]
            node.keys = node.keys[:mid_idx]
            node.values = node.values[:mid_idx + 1]
            for child in new_sibling.values:
                assert child.parent is node, f"Child {child} parent incorrect before update"
                child.parent = new_sibling # type: ignore # Correcting parent reference
            # Assert invariants
            assert len(node.values) == len(node.keys) + 1, f"Original node invariant fail split: K:{len(node.keys)} V:{len(node.values)}"
            assert len(new_sibling.values) == len(new_sibling.keys) + 1, f"Sibling invariant fail split: K:{len(new_sibling.keys)} V:{len(new_sibling.values)}"

        self._insert_in_parent(node, key_to_parent, new_sibling)

    def _insert_in_parent(self, left_child: BPlusTreeNode, key: Any, right_child: BPlusTreeNode) -> None:
        """Inserts key and right_child pointer into parent after a split."""
        parent = left_child.parent

        if parent is None:
            new_root = BPlusTreeNode(self.order, is_leaf=False)
            new_root.keys = [key]
            new_root.values = [left_child, right_child]
            left_child.parent = new_root
            right_child.parent = new_root
            self.root = new_root
            return

        insert_idx = bisect.bisect_left(parent.keys, key)
        parent.keys.insert(insert_idx, key)
        parent.values.insert(insert_idx + 1, right_child)
        right_child.parent = parent

        assert len(parent.values) == len(parent.keys) + 1, f"Parent invariant fail insert: K:{len(parent.keys)} V:{len(parent.values)}"

        if len(parent.keys) == self.order:
            self._split_node(parent)

    def _handle_underflow(self, node: BPlusTreeNode) -> None:
        """Handles node underflow by borrowing or merging."""
        if node.parent is None: # Root Handling
            if not node.is_leaf and not node.keys and len(node.values) == 1:
                self.root = node.values[0] # type: ignore # Make child the new root
                self.root.parent = None
            return

        parent = node.parent
        try:
            child_index = parent.values.index(node)
        except ValueError:
             raise RuntimeError(f"Consistency Error: Node {node} not found in parent {parent}")

        # Try borrowing from left sibling
        if child_index > 0:
            left_sibling = parent.values[child_index - 1]
            if left_sibling.has_excess_keys(self._min_keys): # Use stored min_keys
                self._borrow_from_left(node, left_sibling, parent, child_index)
                return

        # Try borrowing from right sibling
        if child_index < len(parent.values) - 1:
            right_sibling = parent.values[child_index + 1]
            if right_sibling.has_excess_keys(self._min_keys): # Use stored min_keys
                self._borrow_from_right(node, right_sibling, parent, child_index)
                return

        # If borrowing failed, merge
        if child_index > 0: # Merge with left sibling
            left_sibling = parent.values[child_index - 1]
            self._merge_nodes(left_sibling, node, parent, child_index - 1)
        elif child_index < len(parent.values) - 1: # Merge with right sibling
             right_sibling = parent.values[child_index + 1]
             self._merge_nodes(node, right_sibling, parent, child_index)
        else: # Should not happen if root handling correct
            raise RuntimeError(f"Unexpected state in handle_underflow for node {node}")

    def _borrow_from_left(self, node: BPlusTreeNode, left_sibling: BPlusTreeNode, parent: BPlusTreeNode, node_idx_in_parent: int) -> None:
        """Borrows an element from the left sibling."""
        separator_parent_idx = node_idx_in_parent - 1
        if node.is_leaf:
            key_to_move = left_sibling.keys.pop()
            value_to_move = left_sibling.values.pop()
            node.keys.insert(0, key_to_move)
            node.values.insert(0, value_to_move)
            parent.keys[separator_parent_idx] = node.keys[0] # Update parent key
        else: # Internal node
            separator_key = parent.keys[separator_parent_idx]
            node.keys.insert(0, separator_key)
            parent.keys[separator_parent_idx] = left_sibling.keys.pop()
            child_to_move = left_sibling.values.pop()
            node.values.insert(0, child_to_move)
            child_to_move.parent = node # type: ignore # Update parent pointer

        # Assert invariants
        # assert len(left_sibling.values) == len(left_sibling.keys) + (0 if left_sibling.is_leaf else 1)
        # assert len(node.values) == len(node.keys) + (0 if node.is_leaf else 1)


    def _borrow_from_right(self, node: BPlusTreeNode, right_sibling: BPlusTreeNode, parent: BPlusTreeNode, node_idx_in_parent: int) -> None:
        """Borrows an element from the right sibling."""
        separator_parent_idx = node_idx_in_parent
        if node.is_leaf:
            key_to_move = right_sibling.keys.pop(0)
            value_to_move = right_sibling.values.pop(0)
            node.keys.append(key_to_move)
            node.values.append(value_to_move)
            # Update parent separator key
            # Check if sibling has keys left AFTER pop
            parent.keys[separator_parent_idx] = right_sibling.keys[0] if right_sibling.keys else key_to_move
        else: # Internal node
            separator_key = parent.keys[separator_parent_idx]
            node.keys.append(separator_key)
            parent.keys[separator_parent_idx] = right_sibling.keys.pop(0)
            child_to_move = right_sibling.values.pop(0)
            node.values.append(child_to_move)
            child_to_move.parent = node # type: ignore # Update parent pointer

        # Assert invariants
        # assert len(right_sibling.values) == len(right_sibling.keys) + (0 if right_sibling.is_leaf else 1)
        # assert len(node.values) == len(node.keys) + (0 if node.is_leaf else 1)

    def _merge_nodes(self, left_node: BPlusTreeNode, right_node: BPlusTreeNode, parent: BPlusTreeNode, left_node_idx_in_parent: int) -> None:
        """Merges right_node into left_node."""
        separator_key = parent.keys.pop(left_node_idx_in_parent)
        parent.values.pop(left_node_idx_in_parent + 1) # Remove pointer to right node

        if not left_node.is_leaf: # Internal node merge
            left_node.keys.append(separator_key)
            left_node.keys.extend(right_node.keys)
            original_right_values = list(right_node.values) # Copy before extending
            left_node.values.extend(original_right_values)
            for child in original_right_values: # Iterate over the actual moved children
                assert child.parent is right_node, f"Child {child} parent incorrect before merge update"
                child.parent = left_node # type: ignore
        else: # Leaf node merge
            left_node.keys.extend(right_node.keys)
            left_node.values.extend(right_node.values)
            left_node.next_leaf = right_node.next_leaf

        # Assert merged node invariant
        assert len(left_node.values) == len(left_node.keys) + (0 if left_node.is_leaf else 1), \
            f"Merged node invariant fail: L:{left_node.is_leaf} K:{len(left_node.keys)} V:{len(left_node.values)}"

        # Check if parent underflows
        if parent.is_underflow(self._min_keys):
            self._handle_underflow(parent)


    # --- Visualization ---
    def visualize_tree(self):
        """Generates a Graphviz Digraph object using HTML-like labels."""
        try: from graphviz import Digraph
        except ImportError: print("Install graphviz library"); return None

        dot = Digraph(comment='B+ Tree', node_attr={'shape': 'plain'})
        if not self.root or (self.root.is_leaf and not self.root.keys):
            dot.node('empty', 'Tree is empty'); return dot

        node_queue = [(self.root, 'node_root')]
        node_id_map = {self.root: 'node_root'}
        id_counter = 0
        processed_nodes = set()
        all_leaf_render_info = []

        while node_queue:
            current_node, node_id = node_queue.pop(0)
            if current_node in processed_nodes: continue
            processed_nodes.add(current_node)

            # --- HTML Label Generation ---
            html_label = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="2">' # Added padding

            if not current_node.is_leaf: # Internal Node (2-Row HTML)
                 # Row 1: Pointers
                html_label += '<TR>'
                for i in range(len(current_node.values)):
                     html_label += f'<TD PORT="f{i}">P{i}</TD>'
                html_label += '</TR>'
                 # Row 2: Keys (aligned under gaps)
                html_label += '<TR>'
                html_label += '<TD></TD>' # Leading spacer
                for i, key in enumerate(current_node.keys):
                    html_label += f'<TD>{key}</TD><TD></TD>' # Key cell + spacer cell
                html_label += '</TR>'
                html_label += '</TABLE>>'
                dot.node(node_id, label=html_label)

                # Add children & edges
                for i, child in enumerate(current_node.values):
                    if child not in node_id_map:
                        id_counter += 1; child_id = f"node_{id_counter}"; node_id_map[child] = child_id
                    else: child_id = node_id_map[child]
                    if child not in processed_nodes and child not in [n for n, id_str in node_queue]: node_queue.append((child, child_id))
                    dot.edge(f"{node_id}:f{i}", child_id) # Point edge FROM port

            else: # Leaf Node (2-Row HTML)
                if not current_node.keys:
                    html_label += '<TR><TD BGCOLOR="lightblue">Empty Leaf</TD></TR>'
                else:
                    # Row 1: Keys
                    label_keys = '<TR>' + ''.join([f'<TD PORT="k{i}" BGCOLOR="lightblue">{key}</TD>' for i, key in enumerate(current_node.keys)]) + '</TR>'
                    # Row 2: Values
                    label_vals = '<TR>' + ''.join([f'<TD PORT="v{i}" BGCOLOR="lightblue">V({current_node.keys[i]})</TD>' for i in range(len(current_node.keys))]) + '</TR>'
                    html_label += f"{label_keys}{label_vals}"
                html_label += '</TABLE>>'
                dot.node(node_id, label=html_label)
                all_leaf_render_info.append((current_node, node_id))
            # --- End Label Generation ---

        # --- Draw Leaf Links ---
        first_leaf = self.root
        while first_leaf and not first_leaf.is_leaf:
             if not first_leaf.values: break
             first_leaf = first_leaf.values[0] # type: ignore

        obj_to_id = {node_obj: node_str_id for node_obj, node_str_id in all_leaf_render_info}
        visited_leaves = set()
        current_leaf_obj = first_leaf
        while current_leaf_obj and current_leaf_obj not in visited_leaves:
            visited_leaves.add(current_leaf_obj)
            current_leaf_id = obj_to_id.get(current_leaf_obj)
            next_leaf_obj = current_leaf_obj.next_leaf
            next_leaf_id = obj_to_id.get(next_leaf_obj)
            if current_leaf_id and next_leaf_id:
                 dot.edge(f"{current_leaf_id}", f"{next_leaf_id}", style='dashed', arrowhead='none', constraint='false')
            current_leaf_obj = next_leaf_obj
        # --- End Leaf Links ---

        return dot
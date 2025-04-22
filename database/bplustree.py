#db_management_system/database/bplustree.py
import bisect
import math
from typing import Any, List, Optional, Tuple, Union

NodeValue = Union['BPlusTreeNode', Any] # Child node or actual data

class BPlusTreeNode:
    """Represents a node in the B+ Tree (Internal or Leaf)."""
    # (Constructor and __repr__ remain the same as the 'fresh start' version)
    def __init__(self, order: int, parent: Optional['BPlusTreeNode'] = None, is_leaf: bool = False):
        self.order: int = order
        self.parent: Optional[BPlusTreeNode] = parent
        self.keys: List[Any] = []
        self.values: List[NodeValue] = [] # Child nodes for Internal, data values for Leaf
        self.is_leaf: bool = is_leaf
        self.next_leaf: Optional[BPlusTreeNode] = None

    def __repr__(self) -> str:
        key_str = ", ".join(map(str, self.keys))
        return f"Node({'L' if self.is_leaf else 'I'}, K:[{key_str}])"

    def is_full(self) -> bool:
        """Node has max number of keys (order - 1)."""
        return len(self.keys) == self.order - 1

    def has_excess_keys(self, min_keys: int) -> bool:
        """Node has more than the minimum number of keys."""
        return len(self.keys) > min_keys

    def is_underflow(self, min_keys: int) -> bool:
        """Node has less than the minimum number of keys."""
        if self.parent is None: return False
        return len(self.keys) < min_keys

class BPlusTree:
    """B+ Tree Implementation (Optimized Node Lookups)."""
    def __init__(self, order: int = 4):
        if order < 3: raise ValueError("B+ Tree order must be at least 3")
        self.order: int = order
        self.root: BPlusTreeNode = BPlusTreeNode(order, is_leaf=True)
        self._min_keys: int = math.ceil(self.order / 2) - 1 # Stored min keys

    # --- Core Traversal ---
    def _find_leaf(self, key: Any) -> BPlusTreeNode:
        """Find the leaf node where the key should exist using bisect_right."""
        node = self.root
        while not node.is_leaf:
            assert len(node.values) == len(node.keys) + 1, f"Inv Vio: N {node} K {len(node.keys)} V {len(node.values)}"
            idx = bisect.bisect_right(node.keys, key)
            assert idx < len(node.values), f"Idx Err: idx={idx}, len(V)={len(node.values)} N {node}"
            next_node = node.values[idx]
            assert next_node.parent is node, f"Parent Err: C {next_node} P {next_node.parent}, Exp {node}"
            node = next_node # type: ignore
        return node

    # --- Public Operations ---

    def search(self, key: Any) -> Optional[Any]:
        """Search using bisect_left for efficiency."""
        leaf = self._find_leaf(key)
        # Find insertion point for key
        idx = bisect.bisect_left(leaf.keys, key)
        # Check if key at that index actually matches
        if idx < len(leaf.keys) and leaf.keys[idx] == key:
            return leaf.values[idx]
        return None

    def insert(self, key: Any, value: Any) -> None:
        """Insert a key-value pair into the tree."""
        leaf = self._find_leaf(key)
        insert_idx = bisect.bisect_left(leaf.keys, key)
        # Optional: Check for duplicates before inserting
        # if insert_idx < len(leaf.keys) and leaf.keys[insert_idx] == key:
        #     # Handle duplicate (e.g., raise error or update)
        #     # self.update(key, value) # Example update
        #     # return
        #     pass # Current behavior ignores duplicates silently if check omitted
        leaf.keys.insert(insert_idx, key)
        leaf.values.insert(insert_idx, value)
        if len(leaf.keys) == self.order: # Overflow check
            self._split_node(leaf)

    def delete(self, key: Any) -> bool:
        """Delete using bisect_left for lookup."""
        leaf = self._find_leaf(key)
        # Find potential index using bisect_left
        idx = bisect.bisect_left(leaf.keys, key)
        # Verify key exists at that index
        if idx < len(leaf.keys) and leaf.keys[idx] == key:
            leaf.keys.pop(idx)
            leaf.values.pop(idx)
            if leaf.is_underflow(self._min_keys):
                self._handle_underflow(leaf)
            return True # SUCCESS
        else:
            return False # FAILURE: Key not found

    def update(self, key: Any, new_value: Any) -> bool:
        """Update using bisect_left for lookup."""
        leaf = self._find_leaf(key)
        idx = bisect.bisect_left(leaf.keys, key)
        if idx < len(leaf.keys) and leaf.keys[idx] == key:
            leaf.values[idx] = new_value
            return True
        return False # Key not found

    # --- Range Query & Get All (Remain the same - already efficient) ---
    def range_query(self, start_key: Any, end_key: Any) -> List[Tuple[Any, Any]]:
        result: List[Tuple[Any, Any]] = []
        leaf = self._find_leaf(start_key)
        while leaf is not None:
            for i, k in enumerate(leaf.keys):
                if k >= start_key:
                    if k <= end_key: result.append((k, leaf.values[i]))
                    else: return result
            if not leaf.keys or leaf.keys[-1] >= end_key: break
            leaf = leaf.next_leaf
        return result

    def get_all(self) -> List[Tuple[Any, Any]]:
        result: List[Tuple[Any, Any]] = []
        node = self.root
        while not node.is_leaf:
             if not node.values: return []
             node = node.values[0] # type: ignore
        current_leaf: Optional[BPlusTreeNode] = node
        while current_leaf is not None:
            for i, k in enumerate(current_leaf.keys): result.append((k, current_leaf.values[i]))
            current_leaf = current_leaf.next_leaf
        return result

    def _split_node(self, node: BPlusTreeNode) -> None:
        mid_idx = self.order // 2; new_sibling = BPlusTreeNode(self.order, parent=node.parent, is_leaf=node.is_leaf)
        if node.is_leaf:
            key_to_parent = node.keys[mid_idx]; new_sibling.keys = node.keys[mid_idx:]; new_sibling.values = node.values[mid_idx:]
            node.keys = node.keys[:mid_idx]; node.values = node.values[:mid_idx]
            new_sibling.next_leaf = node.next_leaf; node.next_leaf = new_sibling
        else:
            key_to_parent = node.keys[mid_idx]; new_sibling.keys = node.keys[mid_idx + 1:]; new_sibling.values = node.values[mid_idx + 1:]
            node.keys = node.keys[:mid_idx]; node.values = node.values[:mid_idx + 1]
            for child in new_sibling.values: child.parent = new_sibling # type: ignore
            assert len(node.values) == len(node.keys) + 1, "Inv fail split orig"; assert len(new_sibling.values) == len(new_sibling.keys) + 1, "Inv fail split sib"
        self._insert_in_parent(node, key_to_parent, new_sibling)

    def _insert_in_parent(self, left_child: BPlusTreeNode, key: Any, right_child: BPlusTreeNode) -> None:
        parent = left_child.parent
        if parent is None:
            new_root = BPlusTreeNode(self.order, is_leaf=False); new_root.keys = [key]; new_root.values = [left_child, right_child]
            left_child.parent = new_root; right_child.parent = new_root; self.root = new_root; return
        insert_idx = bisect.bisect_left(parent.keys, key); parent.keys.insert(insert_idx, key); parent.values.insert(insert_idx + 1, right_child); right_child.parent = parent
        assert len(parent.values) == len(parent.keys) + 1, "Inv fail insert parent"
        if len(parent.keys) == self.order: self._split_node(parent)

    def _handle_underflow(self, node: BPlusTreeNode) -> None:
        if node.parent is None:
            if not node.is_leaf and not node.keys and len(node.values) == 1: self.root = node.values[0]; self.root.parent = None # type: ignore
            return
        parent = node.parent
        try: child_index = parent.values.index(node)
        except ValueError: raise RuntimeError(f"Consistency Err: N {node} not in P {parent}")
        if child_index > 0: # Try borrow left
            left_sibling = parent.values[child_index - 1]
            if left_sibling.has_excess_keys(self._min_keys): self._borrow_from_left(node, left_sibling, parent, child_index); return
        if child_index < len(parent.values) - 1: # Try borrow right
            right_sibling = parent.values[child_index + 1]
            if right_sibling.has_excess_keys(self._min_keys): self._borrow_from_right(node, right_sibling, parent, child_index); return
        if child_index > 0: # Merge left
            self._merge_nodes(parent.values[child_index - 1], node, parent, child_index - 1)
        elif child_index < len(parent.values) - 1: # Merge right
             self._merge_nodes(node, parent.values[child_index + 1], parent, child_index)
        else: raise RuntimeError(f"Unexpected state in handle_underflow N {node}")

    def _borrow_from_left(self, node: BPlusTreeNode, left_sibling: BPlusTreeNode, parent: BPlusTreeNode, node_idx: int) -> None:
        sep_idx = node_idx - 1
        if node.is_leaf:
            k = left_sibling.keys.pop(); v = left_sibling.values.pop(); node.keys.insert(0, k); node.values.insert(0, v)
            parent.keys[sep_idx] = node.keys[0]
        else:
            sep_k = parent.keys[sep_idx]; node.keys.insert(0, sep_k); parent.keys[sep_idx] = left_sibling.keys.pop()
            child = left_sibling.values.pop(); node.values.insert(0, child); child.parent = node # type: ignore

    def _borrow_from_right(self, node: BPlusTreeNode, right_sibling: BPlusTreeNode, parent: BPlusTreeNode, node_idx: int) -> None:
        sep_idx = node_idx
        if node.is_leaf:
            k = right_sibling.keys.pop(0); v = right_sibling.values.pop(0); node.keys.append(k); node.values.append(v)
            parent.keys[sep_idx] = right_sibling.keys[0] if right_sibling.keys else k
        else:
            sep_k = parent.keys[sep_idx]; node.keys.append(sep_k); parent.keys[sep_idx] = right_sibling.keys.pop(0)
            child = right_sibling.values.pop(0); node.values.append(child); child.parent = node # type: ignore

    def _merge_nodes(self, left_node: BPlusTreeNode, right_node: BPlusTreeNode, parent: BPlusTreeNode, left_idx: int) -> None:
        sep_k = parent.keys.pop(left_idx); parent.values.pop(left_idx + 1)
        if not left_node.is_leaf:
            left_node.keys.append(sep_k); left_node.keys.extend(right_node.keys)
            moved_children = list(right_node.values); left_node.values.extend(moved_children)
            for child in moved_children: child.parent = left_node # type: ignore
        else:
            left_node.keys.extend(right_node.keys); left_node.values.extend(right_node.values)
            left_node.next_leaf = right_node.next_leaf
        assert len(left_node.values) == len(left_node.keys) + (0 if left_node.is_leaf else 1), "Inv fail merge"
        if parent.is_underflow(self._min_keys): self._handle_underflow(parent)

    # --- Visualization (Keep HTML version from previous step) ---
    
    # In class BPlusTree within bplustree.py

    def visualize_tree(self):
        """
        Generates a Graphviz Digraph object for visualization.
        Uses HTML-like labels with single-row internal nodes and detailed leaf nodes.
        """
        try:
            from graphviz import Digraph
        except ImportError:
            print("Install graphviz library and executable for visualization.")
            return None

        # Use node_attr shape='plain' so HTML table defines the shape
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
            # Use border=1 for debugging, 0 for final look
            html_label = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'

            # <<< CORRECTED Internal Node HTML (Single Row: P0 | K1 | P1 | K2 | P2 ...) >>>
            if not current_node.is_leaf:
                html_label += '<TR>'
                html_label += f'<TD PORT="f0">P0</TD>' # First pointer port
                for i, key in enumerate(current_node.keys):
                    html_label += f'<TD>{key}</TD>' # Key cell
                    html_label += f'<TD PORT="f{i+1}">P{i+1}</TD>' # Next pointer port
                html_label += '</TR>'
                html_label += '</TABLE>>'
                dot.node(node_id, label=html_label) # Node uses the HTML label

                # Add children & edges (Connect TO pointer ports f{i})
                for i, child in enumerate(current_node.values):
                    if child not in node_id_map:
                         id_counter += 1; child_id = f"node_{id_counter}"; node_id_map[child] = child_id
                    else: child_id = node_id_map[child]
                    if child not in processed_nodes and child not in [n for n, id_str in node_queue]: node_queue.append((child, child_id))
                    # Ensure edge targets the correct port name defined above
                    dot.edge(f"{node_id}:f{i}", child_id)
            # <<< END CORRECTED Internal Node HTML >>>

            else: # Leaf Node (Detailed View from previous step)
                if not current_node.keys:
                    html_label += '<TR><TD BGCOLOR="lightblue">Empty Leaf</TD></TR>'
                else:
                    # Create one cell per Key-Value pair in the leaf
                    label_content = '<TR>'
                    for i, key in enumerate(current_node.keys):
                        value = current_node.values[i]
                        # Create a compact representation of the record
                        record_repr = f"Key: {key}<BR/>"
                        if isinstance(value, dict):
                            count = 0; max_fields_to_show = 2
                            for rec_key, rec_val in value.items():
                                if rec_key == key: continue # Skip main key
                                val_str = str(rec_val); val_str = (val_str[:8] + '...') if len(val_str) > 10 else val_str
                                record_repr += f"{rec_key}: {val_str}<BR/>"
                                count += 1
                                if count >= max_fields_to_show: break
                        else: record_repr += f"Value: {str(value)[:15]}"
                        # Add cell for this key-record pair
                        label_content += f'<TD PORT="kv{i}" BGCOLOR="lightblue" ALIGN="LEFT">{record_repr}</TD>'
                    label_content += '</TR>'
                    html_label += label_content
                html_label += '</TABLE>>'
                dot.node(node_id, label=html_label)
                all_leaf_render_info.append((current_node, node_id))
            # --- End Label Generation ---

        # --- Draw Leaf Links ---
        # (Leaf linking logic remains the same)
        first_leaf = self.root
        while first_leaf and not first_leaf.is_leaf:
             if not first_leaf.values: break
             first_leaf = first_leaf.values[0] # type: ignore
        obj_to_id = {node_obj: node_str_id for node_obj, node_str_id in all_leaf_render_info}; visited_leaves = set(); current_leaf_obj = first_leaf
        while current_leaf_obj and current_leaf_obj not in visited_leaves:
            visited_leaves.add(current_leaf_obj); current_leaf_id = obj_to_id.get(current_leaf_obj); next_leaf_obj = current_leaf_obj.next_leaf; next_leaf_id = obj_to_id.get(next_leaf_obj)
            if current_leaf_id and next_leaf_id: dot.edge(f"{current_leaf_id}", f"{next_leaf_id}", style='dashed', arrowhead='none', constraint='false')
            current_leaf_obj = next_leaf_obj
        # --- End Leaf Links ---

        return dot
    
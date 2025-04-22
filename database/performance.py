#db_management_system/database/performance.py
import sys
import time
import math
import random
import tracemalloc 
from .bplustree import BPlusTree
from .bruteforce import BruteForceDB

# --- tracemalloc needs careful start/stop ---

class PerformanceAnalyzer:
    """
    Analyzes BPlusTree vs BruteForceDB using separate test methods per operation.
    Uses tracemalloc for peak insertion memory comparison.
    Includes random mix test.
    """

    def __init__(self):
        # Order is now passed to relevant methods, not stored instance-wide
        pass

    def _generate_random_data(self, size, max_key_value=None, sort_keys=False):
        """Generates key-value pairs, optionally sorted."""
        if max_key_value is None: max_key_value = size * 3
        effective_size = min(size, max_key_value)
        if effective_size < size: print(f"Warning: Size {size} > range {max_key_value}. Generating {effective_size} items.")
        keys = random.sample(range(1, max_key_value + 1), effective_size)
        if sort_keys: keys.sort()
        data = [(key, f"value_{key}") for key in keys]
        if not sort_keys: random.shuffle(data)
        return data, keys

    def _trace_and_time_insertion(self, db_class, order, data_pairs):
        """Helper to insert data while tracing memory and timing."""
        # Create instance inside trace block if possible? No, class needed.
        if db_class == BPlusTree:
            instance = db_class(order=order)
        else: # BruteForceDB
            instance = db_class()

        tracemalloc.start()
        t_start = time.perf_counter()
        tracemalloc.reset_peak()

        for key, value in data_pairs:
            instance.insert(key, value)

        t_end = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        insert_time = t_end - t_start
        # Make sure instance is cleaned up if not needed outside
        del instance
        return insert_time, peak

    def run_insertion_memory_time_test(self, data_size, btree_order):
        """
        Tests peak memory (tracemalloc) and time for insertion strategies.

        Returns: dict with keys like 'bf_insert_time', 'bf_peak_mem',
                 'bplus_insert_time_unsorted', 'bplus_peak_mem_unsorted', etc.
        """
        results = {}
        print(f"    Running Insert/Memory Test (Size: {data_size}, Order: {btree_order})...")

        # 1. Brute Force
        bf_data, _ = self._generate_random_data(data_size)
        bf_time, bf_peak = self._trace_and_time_insertion(BruteForceDB, None, bf_data)
        results['bf_insert_time'] = bf_time
        results['bf_peak_mem'] = bf_peak
        del bf_data

        # 2. B+ Tree Unsorted
        unsorted_data, _ = self._generate_random_data(data_size, sort_keys=False)
        unsorted_time, unsorted_peak = self._trace_and_time_insertion(BPlusTree, btree_order, unsorted_data)
        results['bplus_insert_time_unsorted'] = unsorted_time
        results['bplus_peak_mem_unsorted'] = unsorted_peak
        del unsorted_data

        # 3. B+ Tree Sorted
        sorted_data, _ = self._generate_random_data(data_size, sort_keys=True)
        sorted_time, sorted_peak = self._trace_and_time_insertion(BPlusTree, btree_order, sorted_data)
        results['bplus_insert_time_sorted'] = sorted_time
        results['bplus_peak_mem_sorted'] = sorted_peak
        del sorted_data

        print(f"      Peaks (BF/B+U/B+S): {bf_peak}/{unsorted_peak}/{sorted_peak} bytes")
        return results

    # --- Op Timing Tests (Require separate setup now) ---

    def _setup_test_instances(self, data_size, btree_order):
        """Helper to create populated instances for timing tests."""
        data_pairs, keys = self._generate_random_data(data_size, sort_keys=False) # Use unsorted setup
        btree = BPlusTree(order=btree_order)
        bf_db = BruteForceDB()
        for k, v in data_pairs:
            btree.insert(k, v)
            bf_db.insert(k, v)
        return btree, bf_db, keys

    def run_search_test(self, data_size, btree_order):
        """Tests search time."""
        print(f"    Running Search Test (Size: {data_size}, Order: {btree_order})...")
        btree, bf_db, keys_present = self._setup_test_instances(data_size, btree_order)
        if not keys_present: return {'bplus_search_time': 0, 'bf_search_time': 0}
        results = {}
        search_sample_size = min(len(keys_present), max(1000, len(keys_present)//5))
        keys_to_search = random.sample(keys_present, k=search_sample_size)
        t_start = time.perf_counter(); [btree.search(k) for k in keys_to_search]; results['bplus_search_time'] = time.perf_counter() - t_start
        t_start = time.perf_counter(); [bf_db.search(k) for k in keys_to_search]; results['bf_search_time'] = time.perf_counter() - t_start
        results['num_searches'] = search_sample_size
        print(f"      Search (B+/BF): {results['bplus_search_time']:.4f}s / {results['bf_search_time']:.4f}s")
        return results

    def run_range_query_test(self, data_size, btree_order, num_queries=100):
        """Tests range query time."""
        print(f"    Running Range Test (Size: {data_size}, Order: {btree_order})...")
        btree, bf_db, keys_present = self._setup_test_instances(data_size, btree_order)
        if not keys_present or len(keys_present) < 2: return {'bplus_range_time': 0, 'bf_range_time': 0}
        results = {}
        min_k, max_k = min(keys_present), max(keys_present); span = max_k - min_k
        if span <= 0: return {'bplus_range_time': 0, 'bf_range_time': 0}
        queries = []
        for _ in range(num_queries):
             r_size = random.randint(1, max(2, span // 20)); s_k = random.randint(min_k, max(min_k, max_k - r_size)); e_k = s_k + r_size; queries.append((s_k, e_k))
        t_start = time.perf_counter(); [btree.range_query(s, e) for s,e in queries]; results['bplus_range_time'] = time.perf_counter() - t_start
        t_start = time.perf_counter(); [bf_db.range_query(s, e) for s,e in queries]; results['bf_range_time'] = time.perf_counter() - t_start
        print(f"      Range (B+/BF): {results['bplus_range_time']:.4f}s / {results['bf_range_time']:.4f}s")
        return results

    def run_delete_test(self, data_size, btree_order, delete_percentage=30):
        """Tests deletion time."""
        print(f"    Running Delete Test (Size: {data_size}, Order: {btree_order})...")
        btree, bf_db, keys_present = self._setup_test_instances(data_size, btree_order)
        if not keys_present: return {'bplus_delete_time': 0, 'bf_delete_time': 0}
        results = {}
        num_to_delete = int(len(keys_present) * (delete_percentage / 100.0))
        keys_to_delete = random.sample(keys_present, k=min(num_to_delete, len(keys_present)))
        keys_b = list(keys_to_delete); random.shuffle(keys_b)
        keys_f = list(keys_to_delete); random.shuffle(keys_f)
        t_start = time.perf_counter(); [btree.delete(k) for k in keys_b]; results['bplus_delete_time'] = time.perf_counter() - t_start
        t_start = time.perf_counter(); [bf_db.delete(k) for k in keys_f]; results['bf_delete_time'] = time.perf_counter() - t_start
        print(f"      Delete (B+/BF): {results['bplus_delete_time']:.4f}s / {results['bf_delete_time']:.4f}s")
        return results

    def run_random_mix_test(self, data_size, btree_order, num_operations_factor=0.5):
        """Tests time for a random mix of operations."""
        print(f"    Running Mix Test (Size: {data_size}, Order: {btree_order})...")
        btree, bf_db, keys_initial = self._setup_test_instances(data_size, btree_order) # Setup fresh
        results = {}
        num_operations = int(data_size * num_operations_factor)
        current_keys_b = set(keys_initial) # Start with known keys
        max_key_val = data_size * 3
        ops = []
        for _ in range(num_operations): # Generate ops
             op_type = random.choice(['insert', 'search', 'delete'])
             key = None
             if op_type == 'insert': key = random.randint(1, max_key_val); ops.append(('insert', key, f"value_{key}"))
             elif op_type == 'search': key = random.randint(1, max_key_val) if random.random() < 0.3 or not current_keys_b else random.choice(list(current_keys_b)); ops.append(('search', key))
             else: # delete
                  if current_keys_b: key = random.choice(list(current_keys_b)); ops.append(('delete', key))
                  else: key = random.randint(1, max_key_val); ops.append(('insert', key, f"value_{key}")) # Fallback insert

        # Time B+ Tree Mix
        t_start = time.perf_counter()
        temp_keys_b = set(current_keys_b) # Track changes during timed run
        for op in ops:
            op_type, key = op[0], op[1]
            if op_type == 'insert': btree.insert(key, op[2]); temp_keys_b.add(key)
            elif op_type == 'search': btree.search(key)
            elif op_type == 'delete': deleted = btree.delete(key); temp_keys_b.discard(key) if deleted else None # Remove if actually deleted
        results['bplus_mix_time'] = time.perf_counter() - t_start

        # Time Brute Force Mix (Needs its own key tracking)
        temp_keys_f = set(keys_initial)
        t_start = time.perf_counter()
        for op in ops:
             op_type, key = op[0], op[1]
             if op_type == 'insert': bf_db.insert(key, op[2]); temp_keys_f.add(key)
             elif op_type == 'search': bf_db.search(key)
             elif op_type == 'delete': deleted = bf_db.delete(key); temp_keys_f.discard(key) if deleted else None
        results['bf_mix_time'] = time.perf_counter() - t_start

        print(f"      Mix (B+/BF): {results['bplus_mix_time']:.4f}s / {results['bf_mix_time']:.4f}s")
        return results
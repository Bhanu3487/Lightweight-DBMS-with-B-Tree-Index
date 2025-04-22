# File: db_management_system/database/performance.py

import time
import random
import sys
import math
import tracemalloc
from copy import deepcopy

from .bplustree import BPlusTree
from .bruteforce import BruteForceDB

try:
    from pympler import asizeof
    use_pympler = True
except ImportError:
    use_pympler = False
    def asizeof(obj): return sys.getsizeof(obj) # Basic fallback

class PerformanceAnalyzer:
    """
    Analyzes BPlusTree vs BruteForceDB. INDEPENDENT TESTS per operation.
    Compares B+ Tree (Unsorted Build) vs B+ Tree (Sorted Build) vs Brute Force.
    Focuses on Peak Insert Memory (tracemalloc) across orders.
    Times all core operations (Insert, Search, Range, Delete, Update, Mix) across orders.
    """
    def __init__(self):
        pass # Config passed to methods

    def _generate_random_data(self, size, max_key_value=None, sort_keys=False):
        if max_key_value is None: max_key_value = size * 3
        effective_size = min(size, max_key_value)
        if effective_size < size: print(f"Warn: Size {size}>Rng {max_key_value}. Gen {effective_size}.")
        keys = random.sample(range(1, max_key_value + 1), effective_size)
        if sort_keys: keys.sort()
        data_pairs = [(key, f"value_{key*2}") for key in keys] # Make values slightly different
        if not sort_keys: random.shuffle(data_pairs)
        return data_pairs, keys

    def _trace_and_time_insertion(self, db_class, order, data_pairs):
        """Inserts data, returns (insert_time, peak_memory_bytes)."""
        if db_class == BPlusTree: instance = db_class(order=order)
        else: instance = db_class()
        tracemalloc.start(); t_start = time.perf_counter(); tracemalloc.reset_peak()
        for key, value in data_pairs: instance.insert(key, value)
        t_end = time.perf_counter(); _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
        insert_time = t_end - t_start
        del instance
        return insert_time, peak

    def run_insertion_memory_time_test(self, data_size, btree_order):
        """Tests ONLY peak memory and time for INSERTS."""
        results = {}
        print(f"    Ins/Mem Test (Size:{data_size}, Order:{btree_order})...")
        bf_data, _ = self._generate_random_data(data_size)
        bf_time, bf_peak = self._trace_and_time_insertion(BruteForceDB, None, bf_data)
        results['bf_insert_time'] = bf_time; results['bf_peak_mem'] = bf_peak; del bf_data
        uns_data, _ = self._generate_random_data(data_size, sort_keys=False)
        uns_time, uns_peak = self._trace_and_time_insertion(BPlusTree, btree_order, uns_data)
        results['bplus_insert_time_unsorted'] = uns_time; results['bplus_peak_mem_unsorted'] = uns_peak; del uns_data
        sor_data, _ = self._generate_random_data(data_size, sort_keys=True)
        sor_time, sor_peak = self._trace_and_time_insertion(BPlusTree, btree_order, sor_data)
        results['bplus_insert_time_sorted'] = sor_time; results['bplus_peak_mem_sorted'] = sor_peak; del sor_data
        return results

    def _setup_all_for_timing(self, data_size, btree_order):
         """ Helper to create all 3 populated instances needed for one timing test run """
         # Generate base keys
         base_data, base_keys = self._generate_random_data(data_size, sort_keys=False)

         # BF uses unsorted data
         bf_db = BruteForceDB()
         for k, v in base_data: bf_db.insert(k, v)

         # B+ Unsorted uses unsorted data
         btree_unsorted = BPlusTree(order=btree_order) # <<< Variable defined here
         for k, v in base_data: btree_unsorted.insert(k, v)

         # B+ Sorted uses sorted data (built from same keys)
         sorted_data = sorted(base_data, key=lambda item: item[0]) # Sort pairs by key
         btree_sorted = BPlusTree(order=btree_order) # <<< Variable defined here
         for k, v in sorted_data: btree_sorted.insert(k, v)

         return btree_unsorted, btree_sorted, bf_db, base_keys # CORRECT - Return defined variables

    # --- Timing Tests for Other Operations ---

    def run_search_test(self, data_size, btree_order):
        """Tests search time."""
        print(f"    Search Test (Size:{data_size}, Order:{btree_order})...")
        bplus_uns, bplus_sort, bf_db, keys_present = self._setup_all_for_timing(data_size, btree_order)
        if not keys_present: return {'bplus_search_time_unsorted': 0, 'bplus_search_time_sorted': 0, 'bf_search_time': 0}
        results = {}
        sample_size = min(len(keys_present), max(500, len(keys_present)//10)) # Smaller sample
        keys_to_search = random.sample(keys_present, k=sample_size)
        t_start = time.perf_counter(); [bplus_uns.search(k) for k in keys_to_search]; results['bplus_search_time_unsorted'] = time.perf_counter() - t_start
        t_start = time.perf_counter(); [bplus_sort.search(k) for k in keys_to_search]; results['bplus_search_time_sorted'] = time.perf_counter() - t_start
        t_start = time.perf_counter(); [bf_db.search(k) for k in keys_to_search]; results['bf_search_time'] = time.perf_counter() - t_start
        results['num_searches'] = sample_size
        del bplus_uns, bplus_sort, bf_db; return results

    def run_range_query_test(self, data_size, btree_order, num_queries=50): # Fewer queries
        """Tests range query time."""
        print(f"    Range Test (Size:{data_size}, Order:{btree_order})...")
        bplus_uns, bplus_sort, bf_db, keys_present = self._setup_all_for_timing(data_size, btree_order)
        if not keys_present or len(keys_present) < 2: return {'bplus_range_time_unsorted': 0, 'bplus_range_time_sorted': 0, 'bf_range_time': 0}
        results = {}; min_k, max_k = min(keys_present), max(keys_present); span = max_k - min_k
        if span <= 0: return {'bplus_range_time_unsorted': 0, 'bplus_range_time_sorted': 0, 'bf_range_time': 0}
        queries = []
        for _ in range(num_queries):
             r_size = random.randint(1, max(2, span // 20)); s_k = random.randint(min_k, max(min_k, max_k - r_size)); e_k = s_k + r_size; queries.append((s_k, e_k))
        t_start = time.perf_counter(); [bplus_uns.range_query(s, e) for s,e in queries]; results['bplus_range_time_unsorted'] = time.perf_counter() - t_start
        t_start = time.perf_counter(); [bplus_sort.range_query(s, e) for s,e in queries]; results['bplus_range_time_sorted'] = time.perf_counter() - t_start
        t_start = time.perf_counter(); [bf_db.range_query(s, e) for s,e in queries]; results['bf_range_time'] = time.perf_counter() - t_start
        del bplus_uns, bplus_sort, bf_db; return results

    def run_delete_test(self, data_size, btree_order, delete_percentage=20): # Lower %
        """Tests deletion time."""
        print(f"    Delete Test (Size:{data_size}, Order:{btree_order})...")
        bplus_uns, bplus_sort, bf_db, keys_present = self._setup_all_for_timing(data_size, btree_order)
        if not keys_present: return {'bplus_delete_time_unsorted': 0, 'bplus_delete_time_sorted': 0, 'bf_delete_time': 0}
        results = {}
        num_to_delete = int(len(keys_present) * (delete_percentage / 100.0))
        keys_to_delete = random.sample(keys_present, k=min(num_to_delete, len(keys_present)))
        keys_b_uns = list(keys_to_delete); keys_b_sort = list(keys_to_delete); keys_f = list(keys_to_delete)
        random.shuffle(keys_b_uns); random.shuffle(keys_b_sort); random.shuffle(keys_f)
        t_start = time.perf_counter(); [bplus_uns.delete(k) for k in keys_b_uns]; results['bplus_delete_time_unsorted'] = time.perf_counter() - t_start
        t_start = time.perf_counter(); [bplus_sort.delete(k) for k in keys_b_sort]; results['bplus_delete_time_sorted'] = time.perf_counter() - t_start
        t_start = time.perf_counter(); [bf_db.delete(k) for k in keys_f]; results['bf_delete_time'] = time.perf_counter() - t_start
        del bplus_uns, bplus_sort, bf_db; return results

    def run_update_test(self, data_size, btree_order):
        """Tests update time."""
        print(f"    Update Test (Size:{data_size}, Order:{btree_order})...")
        bplus_uns, bplus_sort, bf_db, keys_present = self._setup_all_for_timing(data_size, btree_order)
        if not keys_present: return {'bplus_update_time_unsorted': 0, 'bplus_update_time_sorted': 0, 'bf_update_time': 0}
        results = {}
        sample_size = min(len(keys_present), max(500, len(keys_present)//10)) # Smaller sample
        keys_to_update = random.sample(keys_present, k=sample_size)
        new_vals = [f"upd_{k}" for k in keys_to_update] # Consistent new values
        t_start = time.perf_counter(); [bplus_uns.update(k, v) for k, v in zip(keys_to_update, new_vals)]; results['bplus_update_time_unsorted'] = time.perf_counter() - t_start
        t_start = time.perf_counter(); [bplus_sort.update(k, v) for k, v in zip(keys_to_update, new_vals)]; results['bplus_update_time_sorted'] = time.perf_counter() - t_start
        t_start = time.perf_counter(); [bf_db.update(k, v) for k, v in zip(keys_to_update, new_vals)]; results['bf_update_time'] = time.perf_counter() - t_start
        del bplus_uns, bplus_sort, bf_db; return results

    def run_random_mix_test(self, data_size, btree_order, num_operations_factor=0.3): # Lower factor
        """Tests time for a random mix of operations."""
        print(f"    Mix Test (Size:{data_size}, Order:{btree_order})...")
        bplus_uns, bplus_sort, bf_db, keys_initial = self._setup_all_for_timing(data_size, btree_order)
        if not keys_initial: return {'bplus_mix_time_unsorted': 0, 'bplus_mix_time_sorted': 0, 'bf_mix_time': 0}
        results = {}
        num_operations = int(data_size * num_operations_factor)
        ops = []; op_keys_basis = set(keys_initial); max_key_val = data_size * 3
        for _ in range(num_operations): # Generate ops
             op_type = random.choice(['insert', 'search', 'delete', 'update'])
             key = None
             if op_type == 'insert': key = random.randint(1, max_key_val); ops.append(('insert', key, f"v_{key}"))
             elif op_type == 'search': key = random.randint(1, max_key_val) if random.random() < 0.3 or not op_keys_basis else random.choice(list(op_keys_basis)); ops.append(('search', key))
             elif op_type == 'update':
                  if op_keys_basis: key = random.choice(list(op_keys_basis)); ops.append(('update', key, f"upd_{key}"))
                  else: key = random.randint(1, max_key_val); ops.append(('insert', key, f"v_{key}"))
             else: # delete
                  if op_keys_basis: key = random.choice(list(op_keys_basis)); ops.append(('delete', key)); op_keys_basis.discard(key)
                  else: key = random.randint(1, max_key_val); ops.append(('insert', key, f"v_{key}"))
        # Time B+ Unsorted Mix
        t_start = time.perf_counter()
        for op in ops:
            op_type, key = op[0], op[1]; val = op[2] if len(op)>2 else None
            if op_type == 'insert': bplus_uns.insert(key, val)
            elif op_type == 'search': bplus_uns.search(key)
            elif op_type == 'update': bplus_uns.update(key, val)
            elif op_type == 'delete': bplus_uns.delete(key)
        results['bplus_mix_time_unsorted'] = time.perf_counter() - t_start
        # Time B+ Sorted Mix
        t_start = time.perf_counter()
        for op in ops:
            op_type, key = op[0], op[1]; val = op[2] if len(op)>2 else None
            if op_type == 'insert': bplus_sort.insert(key, val)
            elif op_type == 'search': bplus_sort.search(key)
            elif op_type == 'update': bplus_sort.update(key, val)
            elif op_type == 'delete': bplus_sort.delete(key)
        results['bplus_mix_time_sorted'] = time.perf_counter() - t_start
        # Time Brute Force Mix
        t_start = time.perf_counter()
        for op in ops:
             op_type, key = op[0], op[1]; val = op[2] if len(op)>2 else None
             if op_type == 'insert': bf_db.insert(key, val)
             elif op_type == 'search': bf_db.search(key)
             elif op_type == 'update': bf_db.update(key, val)
             elif op_type == 'delete': bf_db.delete(key)
        results['bf_mix_time'] = time.perf_counter() - t_start
        print(f"      Mix (B+U/B+S/BF): {results['bplus_mix_time_unsorted']:.4f}s / {results['bplus_mix_time_sorted']:.4f}s / {results['bf_mix_time']:.4f}s")
        del bplus_uns, bplus_sort, bf_db; return results
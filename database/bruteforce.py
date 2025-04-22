# File: db_management_system/database/bruteforce.py
import sys

class BruteForceDB:
    """
    Simple list-based storage for key-value pairs.
    Operations use linear search.
    """
    def __init__(self):
        self.data = [] # List of (key, value) tuples

    def insert(self, key, value):
        """Appends key-value pair. Does not check duplicates or order."""
        self.data.append((key, value))

    def search(self, key):
        """Linear search for key, returns value or None."""
        for k, v in self.data:
            if k == key:
                return v
        return None

    def delete(self, key):
        """Removes the first occurrence of the key. Returns True if found, False otherwise."""
        for i, (k, v) in enumerate(self.data):
            if k == key:
                del self.data[i]
                return True
        return False

    def update(self, key, new_value):
        """Updates the value for the first occurrence of key. Returns True/False."""
        for i, (k, v) in enumerate(self.data):
            if k == key:
                self.data[i] = (k, new_value)
                return True
        return False

    def range_query(self, start_key, end_key):
        """Linear scan for keys within the range."""
        return [(k, v) for k, v in self.data if start_key <= k <= end_key]

    def get_all(self):
        """Returns all data."""
        return list(self.data)

    def get_memory_usage(self):
        """Basic memory estimate."""
        return sys.getsizeof(self.data) + sum(sys.getsizeof(item) for item in self.data)
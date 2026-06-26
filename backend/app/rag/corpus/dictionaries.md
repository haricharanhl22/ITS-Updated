# Python Dictionaries — Key-Value Data Structures

## What is a Dictionary?

A dictionary (dict) maps **unique keys** to **values**. Think of it like a real dictionary: you look up a word (key) to get its definition (value).

```python
student = {
    "name": "Alice",
    "age": 21,
    "gpa": 3.85,
    "active": True
}

print(type(student))       # <class 'dict'>
print(len(student))        # 4 key-value pairs
```

Keys must be **immutable** (strings, integers, tuples). Values can be anything.

---

## Accessing Values

```python
config = {"host": "localhost", "port": 5432, "db": "myapp"}

# Direct access — raises KeyError if key missing
print(config["host"])       # localhost

# .get() — returns None (or a default) if key missing
print(config.get("user"))            # None
print(config.get("user", "admin"))   # admin

# Check before accessing
if "port" in config:
    print(config["port"])   # 5432
```

---

## Modifying a Dictionary

```python
person = {"name": "Bob", "age": 30}

# Add or update
person["email"] = "bob@example.com"   # new key
person["age"] = 31                    # update existing

# Delete
del person["email"]

# Remove and return a value
age = person.pop("age")
print(age)      # 31
print(person)   # {'name': 'Bob'}

# Remove last inserted item (Python 3.7+)
person["city"] = "Paris"
person["role"] = "admin"
last = person.popitem()   # ('role', 'admin')
```

---

## Iterating Over a Dictionary

```python
scores = {"Alice": 92, "Bob": 78, "Charlie": 85}

# Keys (default iteration)
for name in scores:
    print(name)

# Keys explicitly
for name in scores.keys():
    print(name)

# Values
for score in scores.values():
    print(score)

# Key-value pairs — most common
for name, score in scores.items():
    print(f"{name}: {score}")
```

---

## Dictionary Methods

```python
d = {"a": 1, "b": 2, "c": 3}

# Merge (Python 3.9+)
extra = {"d": 4, "e": 5}
merged = d | extra     # new dict
d |= extra             # update d in place

# setdefault — only sets if key absent
d.setdefault("f", 0)   # adds "f": 0
d.setdefault("a", 99)  # "a" already exists — no change

# update — add/overwrite from another dict or iterable
d.update({"g": 7, "h": 8})
d.update(i=9, j=10)   # keyword argument syntax

# Copy
shallow = d.copy()
```

---

## Dictionary Comprehensions

```python
# {key_expr: value_expr for item in iterable}

squares = {x: x**2 for x in range(1, 6)}
print(squares)   # {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}

# Filter
even_squares = {x: x**2 for x in range(10) if x % 2 == 0}

# Swap keys and values
original = {"a": 1, "b": 2, "c": 3}
inverted = {v: k for k, v in original.items()}
print(inverted)   # {1: 'a', 2: 'b', 3: 'c'}
```

---

## Nested Dictionaries

```python
users = {
    "alice": {"age": 25, "role": "admin", "score": 92},
    "bob":   {"age": 30, "role": "user",  "score": 78},
}

# Access nested values
print(users["alice"]["role"])    # admin
print(users["bob"]["score"])     # 78

# Safely navigate nested keys
import json
print(json.dumps(users, indent=2))   # pretty-print
```

---

## defaultdict and Counter

```python
from collections import defaultdict, Counter

# defaultdict — auto-creates missing keys
word_lists = defaultdict(list)
word_lists["fruits"].append("apple")
word_lists["fruits"].append("banana")
word_lists["veggies"].append("carrot")
# No KeyError for missing keys

# Counter — count occurrences
text = "the quick brown fox jumps over the lazy dog"
counts = Counter(text.split())
print(counts["the"])          # 2
print(counts.most_common(3))  # [('the', 2), ('quick', 1), ('brown', 1)]
```

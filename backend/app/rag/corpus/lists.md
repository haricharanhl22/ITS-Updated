# Python Lists — Ordered Collections

## What is a List?

A list is an **ordered, mutable** collection that can hold any mix of types. You create one with square brackets:

```python
numbers = [1, 2, 3, 4, 5]
names = ["Alice", "Bob", "Charlie"]
mixed = [42, "hello", True, 3.14, None]
empty = []

print(type(numbers))   # <class 'list'>
print(len(numbers))    # 5
```

**Ordered** means the items have a fixed position (index).  
**Mutable** means you can add, remove, or change items after creation.

---

## Indexing and Slicing

```python
fruits = ["apple", "banana", "cherry", "date", "elderberry"]

# Indexing (0-based)
print(fruits[0])    # apple
print(fruits[-1])   # elderberry (last item)

# Slicing [start:stop:step]
print(fruits[1:3])    # ['banana', 'cherry']
print(fruits[:2])     # ['apple', 'banana']
print(fruits[2:])     # ['cherry', 'date', 'elderberry']
print(fruits[::2])    # ['apple', 'cherry', 'elderberry']
print(fruits[::-1])   # reversed list
```

---

## Modifying a List

Because lists are mutable, you can change them in place:

```python
colours = ["red", "green", "blue"]

# Change an item
colours[1] = "yellow"
print(colours)   # ['red', 'yellow', 'blue']

# Change a slice
colours[0:2] = ["pink", "purple"]
print(colours)   # ['pink', 'purple', 'blue']

# Delete an item
del colours[0]
print(colours)   # ['purple', 'blue']
```

---

## Adding Items

```python
nums = [1, 2, 3]

nums.append(4)          # add to end → [1, 2, 3, 4]
nums.insert(1, 99)      # insert at index 1 → [1, 99, 2, 3, 4]
nums.extend([5, 6])     # add all items from another list → [1, 99, 2, 3, 4, 5, 6]

# Concatenation (creates a new list)
combined = [1, 2] + [3, 4]   # [1, 2, 3, 4]
repeated = [0] * 5            # [0, 0, 0, 0, 0]
```

---

## Removing Items

```python
items = ["a", "b", "c", "b", "d"]

items.remove("b")          # removes FIRST occurrence → ['a', 'c', 'b', 'd']
popped = items.pop()       # removes & returns last item → 'd'; list is ['a','c','b']
popped2 = items.pop(0)     # removes & returns item at index 0 → 'a'; list is ['c','b']
items.clear()              # removes ALL items → []

# Check membership before removing
if "x" in items:
    items.remove("x")
```

---

## Searching and Sorting

```python
nums = [3, 1, 4, 1, 5, 9, 2, 6]

print(nums.index(5))    # 4 — index of first occurrence
print(nums.count(1))    # 2 — how many times 1 appears

# Sort in place (modifies the original list)
nums.sort()
print(nums)   # [1, 1, 2, 3, 4, 5, 6, 9]

nums.sort(reverse=True)
print(nums)   # [9, 6, 5, 4, 3, 2, 1, 1]

# sorted() returns a NEW sorted list (original unchanged)
original = [3, 1, 4]
sorted_copy = sorted(original)
print(original)     # [3, 1, 4] — unchanged
print(sorted_copy)  # [1, 3, 4]

# Sort by custom key
words = ["banana", "fig", "apple", "kiwi"]
words.sort(key=len)         # sort by word length
print(words)   # ['fig', 'kiwi', 'apple', 'banana']
```

---

## List Comprehensions

The most Pythonic way to build a list:

```python
# [expression for item in iterable if condition]

squares = [x**2 for x in range(1, 6)]
print(squares)   # [1, 4, 9, 16, 25]

evens = [x for x in range(20) if x % 2 == 0]
print(evens)   # [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

# Nested comprehension — flatten a 2D list
matrix = [[1, 2], [3, 4], [5, 6]]
flat = [n for row in matrix for n in row]
print(flat)   # [1, 2, 3, 4, 5, 6]
```

---

## Useful Built-in Functions with Lists

```python
nums = [4, 2, 7, 1, 9, 3]

print(len(nums))    # 6
print(sum(nums))    # 26
print(min(nums))    # 1
print(max(nums))    # 9

# any() and all()
print(any(x > 5 for x in nums))    # True (some are > 5)
print(all(x > 0 for x in nums))    # True (all positive)
print(all(x > 5 for x in nums))    # False (not all > 5)
```

---

## Copying a List

```python
original = [1, 2, 3]

# Shallow copy — modifications to copy don't affect original
copy1 = original.copy()
copy2 = original[:]
copy3 = list(original)

copy1.append(4)
print(original)   # [1, 2, 3] — unchanged

# WRONG — this is just another reference to the same list
alias = original
alias.append(99)
print(original)   # [1, 2, 3, 99] — changed!
```

---

## Stack (LIFO) and Queue (FIFO) with Lists

```python
# Stack (Last In, First Out) — use append() and pop()
stack = []
stack.append("first")
stack.append("second")
stack.append("third")
print(stack.pop())   # third (LIFO)
print(stack.pop())   # second

# Queue (First In, First Out) — use collections.deque for efficiency
from collections import deque
queue = deque(["a", "b", "c"])
queue.append("d")
print(queue.popleft())   # a (FIFO)
print(queue.popleft())   # b
```

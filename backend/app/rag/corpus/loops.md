# Python Loops — Iteration from Zero to Hero

## Why Do We Need Loops?

Imagine printing the numbers 1 to 100. Writing 100 `print()` statements is absurd. A loop does it in two lines:

```python
for i in range(1, 101):
    print(i)
```

Loops let you **repeat an action** for every item in a sequence, or **keep running** until a condition is met.

---

## The `for` Loop

The `for` loop iterates over any **iterable** — a list, string, range, or any collection:

```python
# Iterating over a list
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)
# apple
# banana
# cherry

# Iterating over a string
for letter in "Python":
    print(letter)
# P y t h o n (each on its own line)
```

Each time through the loop, the variable (`fruit`, `letter`) holds the current item.

---

## `range()` — Generating Number Sequences

`range()` is the most common way to loop a specific number of times:

```python
# range(stop) — 0 up to (but not including) stop
for i in range(5):
    print(i)   # 0 1 2 3 4

# range(start, stop)
for i in range(2, 6):
    print(i)   # 2 3 4 5

# range(start, stop, step)
for i in range(0, 10, 2):
    print(i)   # 0 2 4 6 8

# Counting backwards
for i in range(5, 0, -1):
    print(i)   # 5 4 3 2 1
```

---

## `enumerate()` — Loop with Index

When you need both the index AND the value:

```python
colours = ["red", "green", "blue"]

for index, colour in enumerate(colours):
    print(f"{index}: {colour}")
# 0: red
# 1: green
# 2: blue

# Start index at 1
for num, colour in enumerate(colours, start=1):
    print(f"{num}. {colour}")
# 1. red
# 2. green
# 3. blue
```

---

## `zip()` — Loop Over Two Lists Together

```python
names = ["Alice", "Bob", "Charlie"]
scores = [92, 78, 85]

for name, score in zip(names, scores):
    print(f"{name} scored {score}")
# Alice scored 92
# Bob scored 78
# Charlie scored 85
```

---

## The `while` Loop

A `while` loop keeps running as long as a condition is `True`:

```python
count = 0
while count < 5:
    print(count)
    count += 1
# 0 1 2 3 4

# Classic "keep asking until valid input"
user_input = ""
while user_input != "quit":
    user_input = input("Type 'quit' to exit: ")
print("Goodbye!")
```

**Warning:** Make sure the condition eventually becomes `False` — otherwise you have an **infinite loop** that freezes your program!

---

## `break` — Exit the Loop Early

`break` immediately stops the loop and jumps past it:

```python
numbers = [1, 3, 7, 2, 9, 4]
target = 7

for num in numbers:
    if num == target:
        print(f"Found {target}!")
        break           # stop as soon as we find it
    print(f"Checking {num}...")
# Checking 1...
# Checking 3...
# Found 7!
```

---

## `continue` — Skip to the Next Iteration

`continue` skips the rest of the current iteration and goes to the next:

```python
for i in range(10):
    if i % 2 == 0:    # skip even numbers
        continue
    print(i)           # only odd numbers print
# 1 3 5 7 9
```

---

## `else` on a Loop

Python's loops have an optional `else` clause — it runs when the loop finishes **without hitting `break`**:

```python
for num in [2, 4, 6, 8]:
    if num % 3 == 0:
        print("Found multiple of 3!")
        break
else:
    print("No multiple of 3 found")   # this runs
```

---

## List Comprehensions — Pythonic Loops

A **list comprehension** is a compact loop that builds a list in one line:

```python
# Traditional loop
squares = []
for x in range(10):
    squares.append(x ** 2)

# List comprehension — same result
squares = [x ** 2 for x in range(10)]
print(squares)   # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# With a condition (filter)
evens = [x for x in range(20) if x % 2 == 0]
print(evens)     # [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

# Transform strings
names = ["alice", "bob", "charlie"]
upper = [n.capitalize() for n in names]
print(upper)   # ['Alice', 'Bob', 'Charlie']
```

---

## Nested Loops

Loops can be nested inside each other:

```python
# Multiplication table
for row in range(1, 4):
    for col in range(1, 4):
        print(f"{row * col:2}", end=" ")
    print()   # newline at end of each row
#  1  2  3
#  2  4  6
#  3  6  9

# Iterating a 2D list (matrix)
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
for row in matrix:
    for cell in row:
        print(cell, end=" ")
    print()
```

---

## Common Loop Patterns

```python
# Sum all numbers in a list
numbers = [5, 12, 7, 3, 18]
total = sum(numbers)   # built-in — always prefer this
# Or manually:
total = 0
for n in numbers:
    total += n

# Find maximum manually
best = numbers[0]
for n in numbers[1:]:
    if n > best:
        best = n
print(best)   # 18

# Filter into a new list
passed = [score for score in [72, 45, 91, 58, 88] if score >= 60]
print(passed)   # [72, 91, 88]
```

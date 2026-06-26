# Python Variables — Complete Beginner's Guide

## What is a Variable?

A variable is a named container that stores a value in your program's memory. Think of it like a labelled box — you put something inside and give it a name so you can find it later.

```python
name = "Alice"
age = 21
score = 95.5
is_student = True
```

Each line above creates a variable. Python figures out the **type** automatically — you never need to declare it. This is called **dynamic typing**.

---

## Variable Naming Rules

Python is strict about names. Follow these rules:

- Must start with a **letter** or **underscore** (`_`)
- Can contain letters, digits, and underscores
- **Case-sensitive** — `Name` and `name` are different variables
- Cannot be a reserved keyword (`for`, `if`, `class`, etc.)

```python
# Valid names
user_name = "Bob"
_private = 42
counter2 = 0
totalAmount = 100   # camelCase works but not Pythonic

# Invalid names — these will crash
2count = 5          # starts with digit
my-var = "test"     # hyphens not allowed
class = "Science"   # reserved keyword
```

Python convention uses **snake_case** for variables (`first_name`, not `firstName`).

---

## Data Types

Python has several built-in types:

| Type | Example | Description |
|------|---------|-------------|
| `int` | `age = 25` | Whole numbers |
| `float` | `price = 9.99` | Decimal numbers |
| `str` | `name = "Alice"` | Text strings |
| `bool` | `active = True` | True or False |
| `None` | `result = None` | Absence of value |

```python
# Check a variable's type
x = 42
print(type(x))       # <class 'int'>

y = 3.14
print(type(y))       # <class 'float'>

z = "hello"
print(type(z))       # <class 'str'>
```

---

## Multiple Assignment

Python lets you assign multiple variables at once:

```python
# Assign the same value to several variables
a = b = c = 0
print(a, b, c)   # 0 0 0

# Unpack a sequence into variables
x, y, z = 1, 2, 3
print(x)   # 1
print(y)   # 2
print(z)   # 3

# Swap two values — no temporary variable needed!
first = "hello"
second = "world"
first, second = second, first
print(first)    # world
print(second)   # hello
```

---

## Type Conversion

You can convert between types using built-in functions:

```python
# String to integer
age_str = "25"
age_int = int(age_str)
print(age_int + 1)    # 26

# Integer to string
score = 100
message = "Score: " + str(score)
print(message)   # Score: 100

# Integer to float
n = 7
f = float(n)
print(f)    # 7.0

# Float to integer (truncates decimal)
pi = 3.99
whole = int(pi)
print(whole)   # 3
```

---

## Constants: Naming by Convention

Python has no built-in `const` keyword. Instead, use **ALL_CAPS** to signal that a value should never change:

```python
MAX_RETRIES = 3
API_URL = "https://api.example.com"
TAX_RATE = 0.08

# Other developers (and your future self) know not to modify these
total = price * (1 + TAX_RATE)
```

---

## Augmented Assignment Operators

These shortcuts modify a variable in place:

```python
count = 0
count += 1    # count = count + 1  →  1
count += 1    # →  2
count -= 1    # count = count - 1  →  1
count *= 3    # count = count * 3  →  3
count //= 2   # integer division   →  1
```

---

## f-Strings: Embedding Variables in Text

The cleanest way to build strings with variable values:

```python
name = "Alice"
age = 21
gpa = 3.85

# f-string — prefix the string with f
intro = f"Hi, I'm {name}, aged {age}, GPA: {gpa:.2f}"
print(intro)
# Hi, I'm Alice, aged 21, GPA: 3.85

# Expressions inside f-strings
print(f"Next year I'll be {age + 1}")
# Next year I'll be 22
```

The `:2f` inside the braces is a **format spec** — it rounds the float to 2 decimal places.

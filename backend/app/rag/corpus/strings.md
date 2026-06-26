# Python Strings — Working with Text

## What is a String?

A string is an **immutable sequence of Unicode characters**. You create one using single, double, or triple quotes:

```python
s1 = 'Hello, World!'
s2 = "Python is fun"
s3 = """This spans
multiple lines"""

# Both quote styles are identical — pick one and be consistent
name = 'Alice'
message = "Welcome, Alice!"
```

Strings are **immutable** — once created, you cannot change a character in place. You always create a new string.

---

## String Length and Indexing

```python
word = "Python"
print(len(word))    # 6 — number of characters

# Positive indexing (left to right, starts at 0)
print(word[0])     # P
print(word[1])     # y
print(word[5])     # n

# Negative indexing (right to left, starts at -1)
print(word[-1])    # n — last character
print(word[-2])    # o
```

---

## Slicing — Extract a Substring

Syntax: `string[start:stop:step]`

```python
s = "Hello, World!"

print(s[0:5])     # Hello (indices 0..4)
print(s[7:12])    # World
print(s[:5])      # Hello (start defaults to 0)
print(s[7:])      # World! (stop defaults to end)
print(s[::2])     # Hlo ol! (every 2nd character)
print(s[::-1])    # !dlroW ,olleH (reversed)
```

---

## String Concatenation and Repetition

```python
first = "Hello"
second = "World"

# Concatenation with +
greeting = first + ", " + second + "!"
print(greeting)   # Hello, World!

# Repetition with *
line = "-" * 20
print(line)       # --------------------

# For many strings, join() is much faster than + in a loop
words = ["Python", "is", "great"]
sentence = " ".join(words)
print(sentence)   # Python is great
```

---

## f-Strings (Formatted String Literals)

The modern, readable way to embed values in strings:

```python
name = "Alice"
age = 25
gpa = 3.875

# Basic embedding
print(f"Name: {name}, Age: {age}")

# Format specifiers
print(f"GPA: {gpa:.2f}")           # 2 decimal places → 3.88
print(f"Age in hex: {age:#x}")     # hex → 0x19
print(f"Name padded: {name:>10}")  # right-align in 10 chars

# Expressions inside braces
print(f"Next year: {age + 1}")
print(f"Upper: {name.upper()}")
```

---

## Essential String Methods

```python
s = "  Hello, World!  "

# Case
print(s.upper())          # "  HELLO, WORLD!  "
print(s.lower())          # "  hello, world!  "
print(s.title())          # "  Hello, World!  "
print(s.capitalize())     # "  hello, world!  " → only first char

# Whitespace
print(s.strip())          # "Hello, World!"  (both ends)
print(s.lstrip())         # "Hello, World!  "  (left only)
print(s.rstrip())         # "  Hello, World!"  (right only)

# Search
print(s.find("World"))    # 9  (index) or -1 if not found
print("World" in s)       # True
print(s.count("l"))       # 3

# Replace
print(s.replace("World", "Python"))  # "  Hello, Python!  "

# Split and join
parts = "a,b,c,d".split(",")   # ['a', 'b', 'c', 'd']
rejoined = "|".join(parts)      # 'a|b|c|d'

# Check content
print("123".isdigit())         # True
print("hello".isalpha())       # True
print("hello world".startswith("hello"))   # True
print("hello world".endswith("world"))     # True
```

---

## String Formatting with format()

Older style, still widely seen in existing code:

```python
name = "Bob"
score = 98.5

# Positional placeholders
print("Hello, {}! Score: {}".format(name, score))

# Named placeholders
print("Hello, {name}! Score: {score:.1f}".format(name=name, score=score))
```

---

## Escape Characters

Special characters inside strings:

```python
print("Line 1\nLine 2")     # newline
print("Tab\there")          # tab
print("She said \"hi\"")    # literal quote
print("C:\\Users\\Alice")   # literal backslash

# Raw string — backslashes are literal (useful for file paths and regex)
path = r"C:\Users\Alice\Documents"
print(path)   # C:\Users\Alice\Documents
```

---

## Multi-line Strings

```python
poem = """
Roses are red,
Violets are blue,
Python is awesome,
And so are you!
"""
print(poem)
```

---

## String Immutability in Practice

```python
word = "hello"
# word[0] = "H"  ← TypeError: strings don't support item assignment

# Instead, build a new string:
word = "H" + word[1:]
print(word)   # Hello
```

Because strings are immutable, `word = word.upper()` doesn't change the original string — it creates a new one and rebinds the name.

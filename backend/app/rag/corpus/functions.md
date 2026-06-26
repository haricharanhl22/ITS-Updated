# Python Functions — The Complete Guide

## What is a Function?

A function is a reusable block of code that performs a specific task. Instead of writing the same logic over and over, you define it once and call it whenever needed.

```python
def greet(name):
    return f"Hello, {name}! Welcome to Python."

print(greet("Alice"))   # Hello, Alice! Welcome to Python.
print(greet("Bob"))     # Hello, Bob! Welcome to Python.
```

Functions make code **shorter**, **easier to read**, and **easier to fix** — change the function once and every call benefits.

---

## Defining a Function

The `def` keyword starts a function definition:

```python
def function_name(parameter1, parameter2):
    # function body — indented by 4 spaces
    result = parameter1 + parameter2
    return result
```

- **`def`** — keyword that declares a function
- **`function_name`** — snake_case name you choose
- **`parameters`** — local variables that receive the caller's arguments
- **`return`** — sends a value back to the caller

If there's no `return` statement, the function returns `None` automatically.

---

## Parameters vs Arguments

These two words are often confused:

- **Parameter** — the variable name in the function definition
- **Argument** — the actual value passed when calling the function

```python
def add(a, b):        # a and b are PARAMETERS
    return a + b

result = add(10, 5)   # 10 and 5 are ARGUMENTS
```

---

## Default Parameter Values

You can give parameters a default value, making them optional:

```python
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

print(greet("Alice"))              # Hello, Alice!
print(greet("Bob", "Good morning")) # Good morning, Bob!
```

Parameters with defaults must come **after** parameters without defaults.

---

## Keyword Arguments

Call a function by naming the parameters — order doesn't matter:

```python
def introduce(name, age, city):
    return f"I'm {name}, {age}, from {city}."

# Positional (order matters)
print(introduce("Alice", 25, "London"))

# Keyword (order doesn't matter)
print(introduce(city="Paris", name="Bob", age=30))
```

---

## *args — Variable Number of Arguments

Use `*args` to accept any number of positional arguments:

```python
def total(*numbers):
    return sum(numbers)

print(total(1, 2, 3))         # 6
print(total(5, 10, 15, 20))   # 50
```

Inside the function, `numbers` is a **tuple** of all the passed values.

---

## **kwargs — Keyword Arguments as a Dictionary

Use `**kwargs` to accept any number of named arguments:

```python
def print_info(**details):
    for key, value in details.items():
        print(f"{key}: {value}")

print_info(name="Alice", age=25, role="student")
# name: Alice
# age: 25
# role: student
```

---

## Return Values

A function can return any type — or even multiple values:

```python
def min_max(numbers):
    return min(numbers), max(numbers)   # returns a tuple

lo, hi = min_max([3, 1, 7, 2, 9])
print(lo, hi)   # 1 9
```

---

## Lambda Functions

A **lambda** is a tiny, anonymous function — perfect for short operations:

```python
# Regular function
def square(x):
    return x ** 2

# Equivalent lambda
square = lambda x: x ** 2

print(square(4))   # 16

# Common with sorted() and map()
names = ["Charlie", "Alice", "Bob"]
names.sort(key=lambda n: len(n))   # sort by name length
print(names)   # ['Bob', 'Alice', 'Charlie']
```

---

## Scope: Local vs Global Variables

Variables created inside a function are **local** — they don't exist outside:

```python
def make_greeting():
    message = "Hello!"   # local variable
    return message

print(make_greeting())   # Hello!
# print(message)         # NameError — message doesn't exist here
```

To use a variable from the outer scope inside a function, use `global` (rarely recommended):

```python
count = 0

def increment():
    global count
    count += 1

increment()
print(count)   # 1
```

---

## Functions as First-Class Objects

In Python, functions are objects — you can store, pass, and return them:

```python
def apply(func, value):
    return func(value)

def double(x):
    return x * 2

result = apply(double, 5)
print(result)   # 10

# Storing a function in a list
operations = [double, lambda x: x ** 2]
for op in operations:
    print(op(3))   # 6, then 9
```

---

## Decorators

A decorator is a function that wraps another function to add behaviour:

```python
def logger(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}...")
        result = func(*args, **kwargs)
        print(f"Done! Result: {result}")
        return result
    return wrapper

@logger
def add(a, b):
    return a + b

add(3, 4)
# Calling add...
# Done! Result: 7
```

The `@logger` syntax is shorthand for `add = logger(add)`.

---

## Docstrings

Document your functions with a **docstring** — a string right after `def`:

```python
def celsius_to_fahrenheit(celsius):
    """Convert Celsius temperature to Fahrenheit.
    
    Args:
        celsius: Temperature in Celsius (float or int)
    
    Returns:
        Temperature in Fahrenheit as a float
    """
    return celsius * 9 / 5 + 32

help(celsius_to_fahrenheit)   # prints the docstring
```

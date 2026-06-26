# Python Error Handling — try, except, finally

## Why Handle Errors?

Programs encounter unexpected situations: files that don't exist, invalid user input, network failures. Without error handling, your program crashes. With it, you can recover gracefully.

```python
# Without error handling — crashes on bad input
age = int(input("Enter age: "))   # ValueError if user types "abc"

# With error handling — handles it gracefully
try:
    age = int(input("Enter age: "))
    print(f"You are {age} years old.")
except ValueError:
    print("Please enter a number!")
```

---

## The try/except Block

```python
try:
    # Code that might raise an exception
    result = 10 / 0
except ZeroDivisionError:
    # Runs only if ZeroDivisionError is raised
    print("Cannot divide by zero!")
```

Python won't crash — it catches the error and runs the `except` block instead.

---

## Catching Multiple Exceptions

```python
def safe_convert(value):
    try:
        return int(value)
    except ValueError:
        print(f"'{value}' is not a valid integer")
        return None
    except TypeError:
        print("Received None — expected a string or number")
        return None

# Catch multiple in one except
try:
    risky_operation()
except (ValueError, KeyError, IndexError) as e:
    print(f"Data error: {e}")
```

---

## The `as` Clause — Inspect the Exception

```python
try:
    numbers = [1, 2, 3]
    print(numbers[10])
except IndexError as e:
    print(f"Index error: {e}")
    # Index error: list index out of range
```

---

## else — Runs When No Exception Occurs

```python
try:
    result = int("42")
except ValueError:
    print("Conversion failed")
else:
    # Only runs if NO exception was raised
    print(f"Conversion succeeded: {result}")
```

---

## finally — Always Runs

Use `finally` for cleanup code that must run whether or not an error occurred:

```python
file = None
try:
    file = open("data.txt", "r")
    content = file.read()
    process(content)
except FileNotFoundError:
    print("File not found!")
except PermissionError:
    print("Cannot read file — check permissions")
finally:
    if file:
        file.close()    # ALWAYS close the file
    print("Done (cleanup ran)")
```

A better pattern uses `with` (context manager) which handles cleanup automatically:

```python
try:
    with open("data.txt") as f:
        content = f.read()
except FileNotFoundError:
    print("File not found!")
# File closes automatically — no need for finally
```

---

## Raising Exceptions

Use `raise` to signal that something went wrong:

```python
def set_age(age):
    if not isinstance(age, int):
        raise TypeError(f"Age must be int, got {type(age).__name__}")
    if age < 0 or age > 150:
        raise ValueError(f"Age must be between 0 and 150, got {age}")
    return age

try:
    set_age(-5)
except ValueError as e:
    print(f"Invalid: {e}")
```

---

## Custom Exception Classes

Create domain-specific exceptions for cleaner code:

```python
class InsufficientFundsError(Exception):
    def __init__(self, balance, amount):
        self.balance = balance
        self.amount = amount
        super().__init__(f"Cannot withdraw {amount}: only {balance} available")

class BankAccount:
    def __init__(self, balance):
        self.balance = balance
    
    def withdraw(self, amount):
        if amount > self.balance:
            raise InsufficientFundsError(self.balance, amount)
        self.balance -= amount

account = BankAccount(100)
try:
    account.withdraw(200)
except InsufficientFundsError as e:
    print(e)   # Cannot withdraw 200: only 100 available
    print(f"Short by: {e.amount - e.balance}")
```

---

## Best Practices

```python
# ✅ Catch specific exceptions
try:
    result = risky()
except ValueError:
    handle_value_error()

# ❌ Never use bare except — it hides bugs
try:
    result = risky()
except:    # catches EVERYTHING including KeyboardInterrupt, SystemExit
    pass

# ✅ Only catch what you can handle
try:
    data = fetch_from_api()
except requests.ConnectionError:
    use_cached_data()
# Let other exceptions propagate naturally

# ✅ Log unexpected errors
import logging
try:
    result = process(data)
except Exception as e:
    logging.error(f"Unexpected error: {e}", exc_info=True)
    raise   # re-raise after logging
```

# Python OOP — Object-Oriented Programming

## What is OOP?

Object-Oriented Programming organises code around **objects** — bundles of data (attributes) and behaviour (methods). Instead of writing separate functions that operate on data, you define a **class** that packages them together.

The four pillars of OOP:
- **Encapsulation** — bundle data and methods, hide internals
- **Inheritance** — a child class reuses parent class code
- **Polymorphism** — different classes respond to the same method call differently
- **Abstraction** — expose only what the caller needs to know

---

## Defining a Class

```python
class Dog:
    # Class attribute — shared by ALL instances
    species = "Canis familiaris"
    
    # __init__ runs automatically when you create an instance
    def __init__(self, name, age):
        # Instance attributes — unique to each dog
        self.name = name
        self.age = age
    
    # Instance method
    def speak(self):
        return f"{self.name} says: Woof!"
    
    def __repr__(self):
        return f"Dog(name={self.name!r}, age={self.age})"
```

`self` is a reference to the current object. Python passes it automatically.

---

## Creating and Using Objects

```python
# Create instances (objects)
rex = Dog("Rex", 3)
bella = Dog("Bella", 5)

# Access attributes
print(rex.name)     # Rex
print(bella.age)    # 5

# Call methods
print(rex.speak())   # Rex says: Woof!
print(bella.speak()) # Bella says: Woof!

# Class attribute shared by all
print(rex.species)   # Canis familiaris
print(Dog.species)   # same
```

---

## Inheritance

A child class inherits all attributes and methods from the parent:

```python
class Animal:
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        raise NotImplementedError("Subclasses must implement speak()")
    
    def __str__(self):
        return f"{type(self).__name__}({self.name})"

class Dog(Animal):
    def speak(self):
        return f"{self.name} says: Woof!"

class Cat(Animal):
    def speak(self):
        return f"{self.name} says: Meow!"

class Duck(Animal):
    def speak(self):
        return f"{self.name} says: Quack!"

animals = [Dog("Rex"), Cat("Whiskers"), Duck("Donald")]
for animal in animals:
    print(animal.speak())   # polymorphism in action!
```

---

## super() — Call the Parent's Method

Use `super()` to extend (not replace) the parent's implementation:

```python
class Vehicle:
    def __init__(self, make, model, year):
        self.make = make
        self.model = model
        self.year = year
    
    def describe(self):
        return f"{self.year} {self.make} {self.model}"

class ElectricVehicle(Vehicle):
    def __init__(self, make, model, year, battery_kw):
        super().__init__(make, model, year)   # call parent __init__
        self.battery_kw = battery_kw          # add new attribute
    
    def describe(self):
        base = super().describe()             # call parent describe()
        return f"{base} (Electric, {self.battery_kw} kW battery)"

tesla = ElectricVehicle("Tesla", "Model 3", 2023, 75)
print(tesla.describe())
# 2023 Tesla Model 3 (Electric, 75 kW battery)
```

---

## Encapsulation — Private Attributes

By convention, prefix with `_` (single) or `__` (double underscore) to signal "don't touch":

```python
class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.__balance = balance   # "private" — name-mangled to _BankAccount__balance
    
    def deposit(self, amount):
        if amount > 0:
            self.__balance += amount
    
    def withdraw(self, amount):
        if 0 < amount <= self.__balance:
            self.__balance -= amount
        else:
            raise ValueError("Insufficient funds")
    
    def get_balance(self):
        return self.__balance
    
    @property
    def balance(self):
        """Read-only property."""
        return self.__balance

acc = BankAccount("Alice", 1000)
acc.deposit(500)
print(acc.balance)     # 1500 (via property)
# acc.__balance          ← AttributeError (protected)
```

---

## Class Methods and Static Methods

```python
class Student:
    total_students = 0   # class variable
    
    def __init__(self, name, grade):
        self.name = name
        self.grade = grade
        Student.total_students += 1
    
    @classmethod
    def get_count(cls):
        """Access/modify class-level state."""
        return cls.total_students
    
    @staticmethod
    def is_passing(grade):
        """Pure utility — no access to instance or class."""
        return grade >= 50

s1 = Student("Alice", 85)
s2 = Student("Bob", 42)

print(Student.get_count())          # 2
print(Student.is_passing(85))       # True
print(Student.is_passing(42))       # False
```

---

## Dunder (Magic) Methods

Special methods surrounded by double underscores give your class built-in behaviour:

```python
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __repr__(self):
        return f"Vector({self.x}, {self.y})"
    
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)
    
    def __len__(self):
        import math
        return int(math.sqrt(self.x**2 + self.y**2))
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

v1 = Vector(2, 3)
v2 = Vector(1, 4)
print(v1 + v2)    # Vector(3, 7)
print(len(v1))    # 3
print(v1 == v2)   # False
```

class Typed:
    def __init__(self, expected_type):
        self.expected_type = expected_type

    def __set_name__(self, name):
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, instance):
        if instance is None:
            return self
        return getattr(instance, self.private_name)

    def __set__(self, instance, value):
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"'{self.name}' wymaga typu {self.expected_type.__name__}, "
                f"otrzymano {type(value).__name__}"
            )
        setattr(instance, self.private_name, value)


class Person:
    name = Typed(str)
    age = Typed(int)

    def __init__(self, name, age):
        self.name = name
        self.age = age


p = Person("Anna", 30)
print(p.name, p.age)   # Anna 30

p.age = "trzydzieści"  # TypeError: 'age' wymaga typu int, otrzymano str
import time
from property_watches import property_watches


class Example:
    class_var = "a class variable"

    def __init__(self):
        self.instance_var = "an instance variable"
        self.prop = "a property"
        self.other_attr = "not watched"

    @property
    def prop(self):
        return self._prop

    @prop.setter
    def prop(self, val):
        self._prop = val

    @property_watches("class_var", "instance_var", "prop")
    def expensive(self) -> str:
        print("<Calculating expensive property...>")
        time.sleep(1)
        return (
            f"{self.class_var}, {self.instance_var}, and {self.prop} walk into a bar."
        )


ex = Example()

print(Example.expensive)

print(ex.expensive)
print(ex.expensive)  # calculates only once

ex.class_var = "an apple"  # invalidates cache

print(ex.expensive)
print(ex.expensive)  # calculates only once

ex.prop = "a banana"  # invalidates cache

print(ex.expensive)
print(ex.expensive)  # calculates only once

ex.instance_var = "a pear"  # invalidates cache

print(ex.expensive)
print(ex.expensive)  # calculates only once

ex.other_attr = "a peach"  # DOES NOT invalidate cache

print(ex.expensive)
print(ex.expensive)  # DOES NOT calculate

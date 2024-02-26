# Property Watches
A cached property that can watch for changes in the attributes it depends on.
The cached value is deleted when the "watched" attributes change.


```python
from property_watches import property_watches

class Example:
    class_var = 3

    def __init__(self):
        self.instance_var = 5
        self.other_attr = 7

    @property_watches("class_var", "instance_var")
    def expensive(self) -> str:
        print("<Calculating expensive property...>")
        time.sleep(1)
        return self.instance_var * self.class_var
```

This example class can be used as follows. The "expensive" attribute is only calculated as needed.

```python

>>>ex = Example()
>>>ex.expensive # calculates and stores in cache
15
>>>ex.expensive # does not recalculate
15
>>>ex.instance_var = 3 # invalidates the cache
>>>ex.expensive # recalculates
9
```

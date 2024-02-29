# Property Watches
A cached property that can watch for changes in the attributes it depends on.
The cached value is deleted when any of the "watched" attributes change.


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
## How it Works

This module defines a @property_watches decorator, which creates a descriptor similar to @property. When accessed, the underlying function is called, and the result is cached in the object under a different name.

When created, the @property_watches secretly converts the "watched" attributes into descriptors, too. They also store their values under a different name. When set, they notify their watchers to clear the cache.
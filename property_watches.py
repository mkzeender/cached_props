from __future__ import annotations
from abc import ABC, abstractmethod
from typing import (
    Callable,
    Generic,
    Protocol,
    Self,
    TypeVar,
    overload,
    runtime_checkable,
    Any,
)

WT = TypeVar("WT")


class DataDescriptor(Protocol, Generic[WT]):
    def __get__(self, obj, objtype=None) -> WT: ...
    def __set__(self, obj, value: WT): ...
    def __delete__(self, obj): ...


_UNSET = object()


class BaseWatchedDescriptor(ABC):
    def __init__(self, name: str, classvar=_UNSET):
        self.classvar = classvar
        self._subscribers = set[PropertyWatcher]()
        self.private_name = "_watched_cache_" + name + ""
        self.name = name

    def subscribe(self, subscriber: PropertyWatcher):
        self._subscribers.add(subscriber)

    @staticmethod
    def from_classvar(name: str, cls_var):
        if hasattr(cls_var, "__get__"):
            if hasattr(cls_var, "__set__") or hasattr(cls_var, "__delete__"):
                # Data descriptor
                return WatchedDescriptor(name, cls_var)
            raise TypeError(
                f"Watched attr '{name}' must be an instance variable, property, DataDescriptor, or other PropertyWatcher, not '{type(cls_var).__name__}'"
            )
        return WatchedAttribute(name, cls_var)

    def _on_change(self, obj):
        for sub in self._subscribers:
            sub.invalidate_cache(obj)

    @abstractmethod
    def __get__(self, obj, objtype=None): ...
    @abstractmethod
    def __delete__(self, obj): ...
    @abstractmethod
    def __set__(self, obj, value): ...


class WatchedDescriptor(BaseWatchedDescriptor):
    classvar: DataDescriptor

    def __get__(self, obj, objtype=None):
        return self.classvar.__get__(obj, objtype)

    def __set__(self, obj, value):
        self.classvar.__set__(obj, value)
        self._on_change(obj)

    def __delete__(self, obj):
        self.classvar.__delete__(obj)
        self._on_change(obj)


class WatchedAttribute(BaseWatchedDescriptor):

    def __get__(self, obj, objtype=None):
        if obj is None:
            if self.classvar is _UNSET:
                raise AttributeError(self.name, objtype)
            return self.classvar
        try:
            return getattr(obj, self.private_name)
        except AttributeError:
            if self.classvar is _UNSET:
                raise AttributeError(self.name, obj) from None
            return self.classvar

    def __delete__(self, obj):
        delattr(obj, self.private_name)
        self._on_change(obj)

    def __set__(self, obj, value):

        setattr(obj, self.private_name, value)
        self._on_change(obj)


PropT = TypeVar("PropT")


class PropertyWatcher(Generic[PropT]):
    def __init__(self, func: Callable[[Any], PropT], watchlist: tuple[str, ...]):
        self.watchlist = watchlist
        self.func = func

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        self.qualname = owner.__qualname__ + "." + name
        self.private_name = "_auto_cached_" + name

        try:
            self.func.__set_name__(owner, name)
        except AttributeError:
            pass

        # we now have a reference to the owner class, so we add subscriptions here!
        for attr_name in self.watchlist:
            self.add_subscription(attr_name, owner)

    @overload
    def __get__(self, obj: None, objtype: type) -> Self: ...
    @overload
    def __get__(self, obj, objtype: type | None = None) -> PropT: ...
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        try:
            val = getattr(obj, self.private_name)
        except AttributeError:
            val = self.func.__get__(obj, objtype)()
            setattr(obj, self.private_name, val)

        return val

    def __set__(self, obj, value: PropT) -> None:
        raise AttributeError(self.name, obj)

    def add_subscription(self, name: str, owner_cls: type) -> None:

        cls_var = owner_cls.__dict__.get(name, _UNSET)  # type: ignore

        if isinstance(cls_var, PropertyWatcher):
            # subscribe to all events that this other watcher is subscribed to.
            for other_name in cls_var.watchlist:
                self.add_subscription(other_name, owner_cls)
            return
        if isinstance(cls_var, BaseWatchedDescriptor):
            cls_var.subscribe(self)
            return

        # implicitly wraps the attribute in a descriptor
        wrapper = BaseWatchedDescriptor.from_classvar(name, cls_var)
        wrapper.subscribe(self)
        setattr(owner_cls, name, wrapper)

    def invalidate_cache(self, obj) -> None:
        try:
            delattr(obj, self.private_name)
        except AttributeError:
            pass

    def __repr__(self):
        return f"<CachedWatcher '{self.qualname}'>"


# PropFunc = TypeVar('PropFunc', bound=Callable[[Any], Any])
T = TypeVar("T")


def property_watches(
    *watched_attrs: str,
) -> Callable[[Callable[[Any], T]], PropertyWatcher[T]]:
    def decorator(func: Callable[[Any], T]) -> PropertyWatcher[T]:
        return PropertyWatcher(func, watched_attrs)

    return decorator

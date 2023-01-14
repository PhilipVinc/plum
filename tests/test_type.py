import typing

import pytest

try:
    from collections.abc import Callable
except ImportError:
    from typing import Callable  # Python 3.8 and earlier

from plum.type import (
    ModuleType,
    PromisedType,
    ResolvableType,
    _is_hint,
    resolve_type_hint,
)


def test_resolvabletype():
    t = ResolvableType("int")
    assert t.__name__ == "int"
    assert t.resolve() is t
    assert t.deliver(int) is t
    assert t.resolve() is int


def test_promisedtype():
    t = PromisedType("int")
    assert t.__name__ == "PromisedType[int]"
    assert t.resolve() is t
    assert t.deliver(int) is t
    assert t.resolve() is int


@pytest.mark.parametrize(
    "module, name, type",
    [
        ("typing", "Union", typing.Union),
        ("__builtin__", "int", int),
        ("__builtins__", "int", int),
        ("builtins", "int", int),
    ],
)
def test_moduletype(module, name, type):
    t = ModuleType(module, name)
    assert t.__name__ == f"ModuleType[{module}.{name}]"
    assert t.resolve() is t
    assert t.retrieve() is t
    assert t.resolve() is type


def test_is_hint():
    assert _is_hint(typing.Union[int, float])
    assert _is_hint(Callable)


@pytest.mark.parametrize(
    "pseudo_int",
    [
        PromisedType("int").deliver(int),
        # We deliver a promised type to a promised type, which means that the
        # resolution must resolve deliveries.
        PromisedType("int").deliver(PromisedType("int").deliver(int)),
        ModuleType("builtins", "int"),
    ],
)
def test_resolve_type_hint(pseudo_int):
    # Test leaves.
    assert resolve_type_hint(None) is None
    assert resolve_type_hint(Ellipsis) is Ellipsis
    assert resolve_type_hint(int) is int

    # Test composition.
    assert resolve_type_hint((pseudo_int, pseudo_int)) == (int, int)
    assert resolve_type_hint([pseudo_int, pseudo_int]) == [int, int]

    def _combo1(fake, real):
        return typing.Union[fake, float], typing.Union[real, float]

    def _combo2(fake, real):
        return Callable[[fake, float], fake], Callable[[real, float], real]

    def _combo3(fake, real):
        return _combo2(*_combo1(fake, real))

    def _combo4(fake, real):
        return _combo3(*_combo2(*_combo1(fake, real)))

    for combo in [_combo1, _combo2, _combo3, _combo4]:
        fake, real = combo(pseudo_int, int)
        assert resolve_type_hint(fake) == real

    class A:
        pass

    # Test warning.
    a = A()
    with pytest.warns(match=r"(?i)could not resolve the type hint"):
        assert resolve_type_hint(a) is a

import plum
from plum import dispatch, PromisedType

myClass = PromisedType("myClass")


@dispatch
def test(a: int, value: myClass = myClass()):
    return value


class MyClass:
    def __init__(self, *args):
        self.a = args

    def __repr__(self):
        return f"MyClass({self.a})"


a = myClass(1)

myClass.deliver(MyClass)

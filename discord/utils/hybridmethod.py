# Source - https://stackoverflow.com/questions/28237955/same-name-for-classmethod-and-instancemethod
# Posted by Martijn Pieters
# Retrieved 11/5/2025, License - CC-BY-SA 4.0

from typing import Callable, Generic, Protocol, TypeVar, overload

from typing_extensions import Concatenate, ParamSpec, Self, override

_T = TypeVar("_T")
_R1_co = TypeVar("_R1_co", covariant=True)
_R2_co = TypeVar("_R2_co", covariant=True)
_P = ParamSpec("_P")


class hybridmethod(Generic[_T, _P, _R1_co, _R2_co]):
    fclass: Callable[Concatenate[type[_T], _P], _R1_co]
    finstance: Callable[Concatenate[_T, _P], _R2_co] | None
    __doc__: str | None
    __isabstractmethod__: bool

    def __init__(
        self,
        fclass: Callable[Concatenate[type[_T], _P], _R1_co],
        finstance: Callable[Concatenate[_T, _P], _R2_co] | None = None,
        doc: str | None = None,
    ):
        self.fclass = fclass
        self.finstance = finstance
        self.__doc__ = doc or fclass.__doc__
        # support use on abstract base classes
        self.__isabstractmethod__ = bool(getattr(fclass, "__isabstractmethod__", False))

    def classmethod(self, fclass: Callable[Concatenate[type[_T], _P], _R1_co]) -> Self:
        return type(self)(fclass, self.finstance, None)

    def instancemethod(self, finstance: Callable[Concatenate[_T, _P], _R2_co]) -> Self:
        return type(self)(self.fclass, finstance, self.__doc__)

    @overload
    def __get__(self, instance: None, cls: type[_T]) -> Callable[_P, _R1_co]: ...

    @overload
    def __get__(self, instance: _T, cls: type[_T] | None = ...) -> Callable[_P, _R1_co] | Callable[_P, _R2_co]: ...

    def __get__(self, instance: _T | None, cls: type[_T] | None = None) -> Callable[_P, _R1_co] | Callable[_P, _R2_co]:
        if instance is None or self.finstance is None:
            # either bound to the class, or no instance method available
            return self.fclass.__get__(cls, None)
        return self.finstance.__get__(instance, cls)

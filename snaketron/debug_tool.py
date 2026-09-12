# -*- coding: utf-8 -*-
"""
Created on Sun Jul 25 17:59:53 2021

@author: Victor Laügt

Version : 3
Implémente des outils pour le debugage : voir help(DebugSpace)
"""
__all__ = ['DebugSpace', 'dbg_outputs_colors']

from time import perf_counter
from inspect import isgeneratorfunction
from os import devnull
import sys
import dataclasses
import colorama

from typing import TypeVar, Union, List, Tuple, Set, Dict, Iterable, Any

NonStaticInstanceMethod = TypeVar('NonStaticInstanceMethod')
ClassMethod = TypeVar('ClassMethod')
StaticInstanceMethod = TypeVar('StaticInstanceMethod')
Function = TypeVar('Function')



class DebugError(Exception) :
    """Exception levée quand les outils de debugage de ce module sont mal
    utilisés
    """

class TagError(DebugError, KeyError) :
    """Exception levée quand l'utilisateur essaie d'acceder à un tag
    inexistant dans l'historique de debugage
    """

class TrackerError(DebugError, TypeError) :
    """Exception levée quand l'utilisateur crée un tracker avec des paramètres
    incorrects
    """

class ConfigError(DebugError, TypeError) :
    """Exception levée quand l'utilisateur essaie de créer ou de reconfigurer
    un espace de débugage avec des paramètres incorrects
    """

def _pass_func(*args, **kwargs) :
    pass



# --- colored messages
@dataclasses.dataclass
class ColorPalette :
    """Implémente des palettes de couleurs. Ce sont des objets qui stockent
    le jeu de couleur des messages de debugage
    """
    symbol : str = colorama.Fore.BLUE + colorama.Style.BRIGHT
    arrow : str = colorama.Fore.MAGENTA + colorama.Style.BRIGHT
    error : str = colorama.Fore.RED + colorama.Style.BRIGHT
    undef : str = colorama.Fore.YELLOW + colorama.Style.BRIGHT
    time : str = colorama.Fore.WHITE
    generator : str = colorama.Fore.GREEN + colorama.Style.BRIGHT
    dbreak : str = colorama.Fore.BLUE + colorama.Back.GREEN
    regular : str = colorama.Style.RESET_ALL

colors = ColorPalette() # Palette de couleur par défaut

def _symbol_color(txt) -> str :
    return f'{colors.symbol}{txt}{colors.regular}'

def _arrow_color(txt) -> str :
    return f'{colors.arrow}{txt}{colors.regular}'

def _error_color(txt) -> str :
    return f'{colors.error}{txt}{colors.regular}'

def _undef_color(txt, original_color=None) -> str :
    return f'{colors.undef}{txt}{original_color or colors.regular}'

def _time_color(txt) -> str :
    return f'{colors.time}{txt}{colors.regular}'

def _generator_color(txt) -> str :
    return f'{colors.generator}{txt}{colors.regular}'

def _break_color(txt) -> str :
    return f'{colors.dbreak}{txt}{colors.regular}'



# --- obj repr tools
def _genericrepr(obj) -> str :
    try :
        return f'<{type(obj).__qualname__} object>'
    except :
        return '<object>'


def _repr(obj) -> Union[Tuple[str, None], Tuple[None, str]] :
    try :
        return repr(obj), None
    except :
        return None, _genericrepr(obj)


def _typerepr(obj) -> Union[Tuple[str, None], Tuple[None, str]] :
    try :
        return type(obj).__qualname__, None
    except :
        return None, '<type>'


def _limitedview(txt:str, char_limit:int=50, line_limit:int=20) -> str :
    """Renvoi une version tronquée d'un texte si celui-ci est trop volumineux
    char_limit : longueur à partir de laquelle une ligne du texte est tronquée
    line_limit : nombre de ligne à partir de laquelle certaines lignes sont
        masquées dans le texte tronqué
    """
    lines = txt.splitlines()
    if len(lines) > line_limit :
        n = line_limit//3
        lines = [*lines[:n], '...', *lines[-n:]]
    for i, l in enumerate(lines) :
        n = char_limit // 3
        if len(l) > char_limit :
            lines[i] = f'{l[:n]}...{l[-n:]}'
    return '\n'.join(lines)


class _ObjRepr :
    """Une instance de _ObjRepr est une représentation textuelle qui décrit
    l'état d'un objet python à un instant donné de l'execution du programme à
    debuguer. Une instance de _ObjRepr ne fait que mémoriser une représentation
    de l'objet, mais sa valeur n'est pas conservée. De plus, si la valeur de
    l'objet est modifiée après l'instanciation de sa représentation _ObjRepr,
    alors cette dernière n'est pas modifiée.
    Attributs :
      value (str) : représentation textuelle de la valeur de l'objet
      type (str) : représentation textuelle du type de l'objet
    """
    __slots__ = ('_valuerepr', '_typerepr', '_generic_valuerepr', '_generic_typerepr')
    def __init__(self, value:Any) :
        self._valuerepr, self._generic_valuerepr = _repr(value)
        self._typerepr, self._generic_typerepr = _typerepr(value)

    @property
    def value(self) :
        value_repr = self._valuerepr
        if value_repr is not None :
            return _limitedview(value_repr)
        return _undef_color(self._generic_valuerepr)

    @property
    def type(self) :
        type_repr = self._typerepr
        if type_repr is not None :
            return _limitedview(type_repr)
        return _undef_color(self._generic_typerepr)

    def __repr__(self) :
        return f"ObjRepr(type={_limitedview(self.type)}, "+\
            f"value={_limitedview(self.value)})"


class _Arg(_ObjRepr) :
    """Représentation _ObjRepr d'un argument positionel de fonction ou méthode
    Attributs :
      value (str) : représentation textuelle de la valeur de l'argument
      type (str) : représentation textuelle du type de l'argument
    """
    __slots__ = ()
    def __init__(self, value:Any, hidden:bool) :
        if hidden :
            self._valuerepr, self._generic_valuerepr = None, _genericrepr(value)
        else :
            self._valuerepr, self._generic_typerepr = _repr(value)
        self._typerepr, self._generic_typerepr = _typerepr(value)

    def __repr__(self) :
        return f"PosArg(type={_limitedview(self.type)}, "+\
            f"value={_limitedview(self.value)})"


class _Kwarg(_Arg) :
    """Représentation _ObjRepr d'un argument à mot-clé de fonction ou méthode
    Attributs :
      name (str) : nom de l'argument
      value (str) : représentation textuelle de la valeur de l'argument
      type (str) : représentation textuelle du type de l'argument
    """
    __slots__ = ('_name', )
    def __init__(self, name:str, value:Any, hidden:bool) :
        self._name = name
        if hidden :
            self._valuerepr, self._generic_valuerepr = None, _genericrepr(value)
        else :
            self._valuerepr, self._generic_typerepr = _repr(value)
        self._typerepr, self._generic_typerepr = _typerepr(value)


    @property
    def name(self) :
        return _limitedview(self._name)

    def __repr__(self) :
        return f"KeyWordArg(name={_limitedview(self._name)}, "+\
         f"type={_limitedview(self.type)}, value={_limitedview(self.value)})"


class _Result(_ObjRepr) :
    """Représentation _ObjRepr du résultat d'une fonction ou méthode
    Attributs :
      value (str) : représentation textuelle de la valeur du résultat
      type (str) : représentation textuelle du type du résultat
    """
    __slots__ = ()
    def __repr__(self) :
        return f"Result(type={_limitedview(self.type)}, "+\
            f"value={_limitedview(self.value)})"


class _Sended(_ObjRepr) :
    """Représentation _ObjRepr d'un élement envoyé à un générateur via sa
    méthode .send()
    Attributs :
      value (str) : représentation textuelle de la valeur du résultat
      type (str) : représentation textuelle du type du résultat
    """
    __slots__ = ()
    def __repr__(self) :
        return f"Sended(type={_limitedview(self.type)}, "+\
            f"value={_limitedview(self.value)})"


class _Yielded(_ObjRepr) :
    """Représentation _ObjRepr d'un élement généré par un générateur
    Attributs :
      value (str) : représentation textuelle de la valeur du résultat
      type (str) : représentation textuelle du type du résultat
    """
    __slots__ = ()
    def __repr__(self) :
        return f"Yielded(type={_limitedview(self.type)}, "+\
            f"value={_limitedview(self.value)})"


class _RaisedException(_ObjRepr) :
    """Représentation _ObjRepr d'une exception levée par une fonction ou méthode
    Attributs :
      value (str) : représentation textuelle de l'exception
      type (str) : représentation textuelle du type de l'exception
      args (tuple of _ObjRepr) : représentations _ObjRepr des arguments de
    l'exception
    """
    __slots__ = ('args')
    def __init__(self, value:Exception) :
        self._valuerepr, self._generic_valuerepr = _repr(value)
        self._typerepr, self._generic_typerepr = _typerepr(value)
        self.args = tuple(_ObjRepr(arg) for arg in value.args)

    def __bool__(self) :
        return False

    def __repr__(self) :
        return f"RaisedException(type={_limitedview(self.type)}, "+\
            f"args={', '.join(arg.value for arg in self.args)})"




# --- dbg histories # TODO : essayer d'implementer les __slots__ dans les classes _<...>Entry
# ------ call entries
class _CallEntry :
    """Un objet _CallEntry est une entrée qui correspond à l'enregistrement de
    l'appel d'une fonction dans un historique de debugage

    Un objet _CallEntry représente l'appel d'une fonction et le résultat de
    son execution

    Attributs
    -------------------------
    f : str
        nom de la fonction ou méthode qui a été appellée
    args : tuple of _Arg
        tuple qui contient les représentations des arguments positionels avec
        lesquels la fonction ou méthode a été appelée
    kwargs : dict of _Kwarg
        dictionnaire qui contient les représentations des arguments à mots clés
        avec lesquels la fonction ou méthode a été appelée
    call_level : int
        niveau d'appel de la fonction ou méthode
    result : _Result
        représentation du résultat de la fonction ou méthode
    exectime : float, None
        durée d'execution de la fonction ou méthode (si celle-ci a été chronométrée)
    """
    __slots__ = ('f', 'args', 'kwargs', 'call_level', '__dict__')
    result = None # resultat de l'execution de la fonction
    exectime = None # durée de l'execution de la fonction

    @property
    def arrow(self) :
        """flèche colorée"""
        return _arrow_color('-->')

    def __new__(cls, args:tuple, kwargs:dict, hargs:set, func_name:str, call_level:int) :
        self = object.__new__(cls)
        # nom de la fonction ou méthode appellée :
        self.f = func_name
        # niveau d'appel :
        self.call_level = call_level
        # arguments à mots-clés passés lors de l'appel :
        self.kwargs = [_Kwarg(name, value, (name in hargs))\
                       for name, value in kwargs.items()]
        return self

    def __init__(self, args:tuple, kwargs:dict, hargs:set, *_) :
        # arguments positionels passés lors de l'appel :
        self.args = [_Arg(value, (i in hargs)) for i, value in enumerate(args)]

    def _returns(self, result, exectime) :
        self.result = _Result(result)
        self.exectime = exectime

    def _error(self, err) :
        self.result = _RaisedException(err)
        return err

    def _args_repr(self) -> List[str] :
        # arguments positionels
        arguments = [arg.value for arg in self.args]
        # arguments à mot-clé
        arguments.extend(f'{arg.name}={arg.value}' for arg in self.kwargs)
        return arguments

    def _call_repr(self) -> str :
        return f"{self.f}({', '.join(self._args_repr())})"

    def _return_repr(self) -> str :
        if self.result :
            res = f"{self.arrow} {_limitedview(self.result.value)}"
        else :
            res = _error_color(f"/!\\ {_limitedview(self.result.value)} /!\\")
        if self.exectime is None :
            return res
        return res + _time_color(f' executed in {self.exectime}s')

    def __repr__(self) :
        if self.result is not None :
            return self._call_repr() + '\n' + self._return_repr()
        return self._call_repr() +\
            _error_color('\n/!\\ unfinished execution /!\\')


class _SelfCallEntry(_CallEntry) :
    __slots__ = ()

    @property
    def first(self) :
        """représentation du premier argument des appels de méthodes d'instance"""
        return _undef_color('<self>')

    def __init__(self, args:tuple, kwargs:dict, hargs:set, *_) :
        # arguments positionels passés lors de l'appel :
        self.args = [_Arg(value, (i in hargs)) for i, value in enumerate(args[1:])]

    def _call_repr(self) -> str :
        arguments = self._args_repr()
        if arguments :
            return f"{self.f}({self.first}, {', '.join(arguments)})"
        return f"{self.f}({self.first})"


class _ClsCallEntry(_SelfCallEntry) :
    __slots__ = ()

    @property
    def first(self) :
        """représentation du premier argument des appels de méthodes de classe"""
        return _undef_color('<cls>')



# ------ generator entries
class _GeneratorEntry(_CallEntry) : # TODO : dans _GeneratorEntry, faire en sorte que les temps d'executions None ne soient pas stockés en mémoire dans le cas où l'execution n'est pas chronometrée
    @property
    def arrow(self) :
        """flèche colorée"""
        return _arrow_color('->')

    @property
    def name(self) :
        """représentation du générateur créé """
        return _generator_color(f'\\{super()._call_repr()}\\')

    def __new__(cls, args:tuple, kwargs:dict, hargs:set, func_name:str) :
        self = object.__new__(cls)
        # nom de la fonction ou méthode génératrice appelée :
        self.f = func_name
        # arguments à mots-clés passés lors de l'appel :
        self.kwargs = [_Kwarg(name, value, (name in hargs))\
                       for name, value in kwargs.items()]

        # objets reçus via la méthode .send(obj) du générateur :
        self.received_elems = []
        # élements générés par le générateur :
        self.yielded_elems = []
        # durées des executions :
        self.exectimes_list = []
        return self

    def __init__(self, args:tuple, kwargs:dict, hargs:set, func_name:str) :
        # arguments positionels passés lors de l'appel :
        self.args = [_Arg(value, (i in hargs)) for i, value in enumerate(args)]

    def _sends(self, sended) :
        self.received_elems.append(_Sended(sended))

    def _yields(self, yielded, exectime) :
        self.yielded_elems.append(_Yielded(yielded))
        self.exectimes_list.append(exectime)

    def _error(self, err) :
        self.yielded_elems.append(_RaisedException(err))
        self.exectimes_list.append(None)
        return err

    def _send_repr(self, index:int=-1) -> str :
        return f'{_limitedview(self.received_elems[index].value)} {self.arrow} {self.name}'

    def _yield_repr(self, index:int=-1) -> str :
        yielded, exectime = self.yielded_elems[index], self.exectimes_list[index]
        if yielded :
            res = f'{self.name} {self.arrow} {_limitedview(yielded.value)}'
        else :
            res = f'{self.name} ' + _error_color(f'/!\\ {yielded.value} /!\\')
        if exectime is None :
            return res
        return res + _time_color(f' executed in {exectime}s')

    def __repr__(self) :
        received = self.received_elems
        yielded = self.yielded_elems
        lines = [f'{self.name} started']
        n = min(len(received), len(yielded))
        for i in range(n) :
            lines.append(self._send_repr(i))
            lines.append(self._yield_repr(i))
        if n != len(yielded) :
            lines.append(_error_color('/!\\ unfinished execution /!\\'))
        return '\n'.join(lines)


class _SelfGeneratorEntry(_GeneratorEntry, _SelfCallEntry) :
    @property
    def first(self) :
        """représentation du premier argument des appels de méthodes d'instance"""
        return _undef_color('<self>', colors.generator)

    def __init__(self, args:tuple, kwargs:dict, hargs:set, func_name:str) :
        # arguments positionels passés lors de l'appel :
        self.args = [_Arg(value, (i in hargs)) for i, value in enumerate(args[1:])]


class _ClsGeneratorEntry(_SelfGeneratorEntry, _ClsCallEntry) :
    @property
    def first(self) :
        """représentation du premier argument des appels de méthodes de classe"""
        return _undef_color('<cls>', colors.generator)



# ------ entry lists
class _EntryList :
    def __init__(self, entries:list, sep:str) :
        self.entries = entries
        self.sep = sep

    def __repr__(self) :
        if len(self) > 55 :
            sep = self.sep
            return sep.join(map(str, self.entries[:25])) + f'{sep}...{sep}' +\
                sep.join(map(str, self.entries[-25:]))
        return self.sep.join(map(str, self.entries))

    def __len__(self) :
        return len(self.entries)

    def __getitem__(self, index) :
        if isinstance(index, slice) :
            return _EntryList(self.entries[index], sep=self.sep)
        return self.entries[index]

    def clear(self) :
        self.entries.clear()


class _TagList :
    __slots__ = ('_tags', '_calls')

    def __init__(self, tags:Dict[str, list], calls:List[_CallEntry]) :
        self._tags = tags
        self._calls = calls

    def __getitem__(self, tag:str) -> _EntryList :
        lst = self._tags.get(tag)
        if lst is None : raise TagError(f"tag non-trouvé : {tag}")
        return _EntryList((self._calls[n] for n in lst), sep='\n\n')

    def __repr__(self) :
        return "<debug space>.history.tags[<tag name>] -> liste des appels de "+\
            "fonctions ou méthodes enregistrés et associés au tag <tag name>"


class _DebugHistory :
    """Implémente des historiques de debugage
    dbg.history est l'historique de debugage de l'espace de debugage dbg

    L'historique de debugage contient trois catégories :
      dbg.history.messages -> liste des messages de debugages enregistrés
      dbg.history.calls -> liste des appels de fonctions ou méthodes enregistrés
      dbg.history.tags['foo'] -> liste des appels de fonctions ou méthodes
                                 enregistrés et associés au tag 'foo'
    """
    __slots__ = ('_messages', '_calls', '_tags')

    def __init__(self) :
        self._messages : List[str] = []
        self._calls : List[str] = []
        self._tags : Dict[str, list] = {}


    def __repr__(self) :
        return """historique de debugage (voir help(DebugSpace.history))"""


    @property
    def messages(self) -> _EntryList :
        return _EntryList(self._messages, sep='\n')
    @property
    def calls(self) -> _EntryList :
        return _EntryList(self._calls, sep='\n\n')
    @property
    def tags(self) -> _TagList :
        return _TagList(self._tags, self._calls)


    def _add_message(self, msg:str) :
        self._messages.append(msg)


    def _add_call(self, entry:_CallEntry, tags:Tuple[str]) :
        n = len(self._calls)
        for tag in tags :
            lst = self._tags.get(tag)
            if lst is not None : lst.append(n)
            else : self._tags[tag] = [n]
        self._calls.append(entry)




# --- trackers
# ------ tracked objects
class _TrackedFunction :
    """Les décorateurs DebugSpace.trackfunc(...)
    et DebugSpace.trackstaticmethod(...) renvoient des objets de type
    _TrackedFunction
    """
    __slots__ = ('_track_off', '_track_on', '_callback')

    def __init__(self, f, decorated_f, enable_track:bool) :
        self._track_off = f
        self._track_on = decorated_f
        self._setcallmode(enable_track)

    @property
    def __doc__(self) :
        return self._track_off.__doc__

    def __repr__(self) :
        return f'{type(self).__name__}({self.__qualname__})'

    def _setcallmode(self, track:bool) :
        if track : self._callback = self._track_on
        else : self._callback = self._track_off

    def __call__(self, *args, **kwargs) :
        return self._callback(*args, **kwargs)

    def __getattr__(self, attrname) :
        return getattr(self._track_off, attrname)


class _TrackedSelfMethod(_TrackedFunction) :
    """Les décorateurs DebugSpace.trackmethod(...) renvoient des objets de type
    _TrackefSelfMethod
    """
    __slots__ = ()

    def __get__(self, instance, owner) :
        # on accède à la méthode d'instance depuis la classe de l'instance
        if instance is None :
            return self._callback

        # on accède à la méthode d'instance depuis l'instance
        return lambda *args, **kwargs : self._callback(instance, *args, **kwargs)


class _TrackedClsMethod(_TrackedFunction) :
    """Les décorateurs DebugSpace.trackclassmethod(...) renvoient des objets de
    type _TrackedClsMethod
    """
    __slots__ = ()

    def __get__(self, instance, owner) :
        # on accède à la méthode de classe depuis l'instance ou depuis la
        # classe de l'instance
        return lambda *args, **kwargs : self._callback(owner, *args, **kwargs)



# ------ tracker objects
class _Tracker :
    """Les décorateurs DebugSpace.trackfunc(...), DebugSpace.trackmethod(...),
    DebugSpace.trackclassmethod(...) et DebugSpace.trackstaticmethod(...) sont
    des instances de la classe _Tracker
    """
    __slots__ = ('debugspace', 'tags', 'hargs', 'yieldfunc', 'exec_func',\
                 'exec_iter')

    def __init__(self, debugspace, tags:Tuple[str], hargs:Set[Union[int, str]],\
                 chrono:bool, yieldfunc:bool) :
        self.debugspace = debugspace
        self.tags = tags
        self.hargs = hargs
        if chrono :
            self.exec_func = self.exec_func_with_chrono
            self.exec_iter = self.exec_iter_with_chrono
        else :
            self.exec_func = self.exec_func_without_chrono
            self.exec_iter = self.exec_iter_without_chrono
        self.yieldfunc = yieldfunc

    def __call__(self, f) -> Union[_TrackedFunction,\
                                   _TrackedSelfMethod,\
                                   _TrackedClsMethod] :
        if self.yieldfunc : return self._yield_func_decorator(f)
        return self._return_func_decorator(f)

    @staticmethod
    def exec_func_without_chrono(f, args, kwargs) :
        return f(*args, **kwargs), None

    @staticmethod
    def exec_func_with_chrono(f, args, kwargs) :
        start = perf_counter()
        result = f(*args, **kwargs)
        stop = perf_counter()
        return result, stop-start

    def exec_iter_without_chrono(self, f, args, kwargs, entry) :
        itr = f(*args, **kwargs)
        received = None
        try :
            while True :
                entry._sends(received)
                self.debugspace._print_send(entry)

                elem = itr.send(received)

                entry._yields(elem, None)
                self.debugspace._print_yield(entry)
                received = yield elem
        except StopIteration :
            return
        except Exception as err :
            entry._error(err)
            self.debugspace._print_yield(entry)
            raise # si une exception a été levée, elle est propagée

    def exec_iter_with_chrono(self, f, args, kwargs, entry) :
        itr = f(*args, **kwargs)
        received = None
        try :
            while True :
                entry._sends(received)
                self.debugspace._print_send(entry)

                start = perf_counter()
                elem = itr.send(received)
                stop = perf_counter()

                entry._yields(elem, stop-start)
                self.debugspace._print_yield(entry)
                received = yield elem
        except StopIteration :
            return
        except Exception as err :
            entry._error(err)
            self.debugspace._print_yield(entry)
            raise # si une exception a été levée, elle est propagée



def tracker_type_builder(name:str, _TrackedCallableType:type,\
                         _CallEntryType:type, _GeneratorEntryType:type) -> type :
    """Fonction qui permet de construire les différents types de trackers.
    Tous les types de trackers héritent du type _Tracker
    """
    class _TrackerType(_Tracker) :
        __slots__ = ()

        def _return_func_decorator(self, f) -> _TrackedCallableType :
            """Renvoi une fonction qui exécute f en même temps de suivre son
            exécution
            """
            def decorated(*args, **kwargs) :
                # appel de f
                self.debugspace._level += 1
                entry = _CallEntryType(args,\
                                       kwargs,\
                                       self.hargs,\
                                       f.__qualname__,\
                                       self.debugspace._level)
                self.debugspace.history._add_call(entry, self.tags)
                self.debugspace._print_call(entry)


                # execution de f
                try :
                    result, t = self.exec_func(f, args, kwargs)
                except Exception as err :
                    error = entry._error(err)
                else :
                    error = entry._returns(result, t)

                # retour du résultat de f
                self.debugspace._print_return(entry)
                self.debugspace._level -= 1
                if error :
                    raise error # si une exception a été levée, elle est propagée
                return result

            tracked = _TrackedCallableType(f,\
                                           decorated,\
                                           self.debugspace._config.trackers)
            self.debugspace._TRACKED.append(tracked)
            return tracked


        def _yield_func_decorator(self, f) -> _TrackedCallableType :
            """Renvoi une fonction qui renvoi les genérateurs que crée f et qui
            suit leur exécutions
            """
            if not isgeneratorfunction(f) :
                raise TrackerError(f"{self} devrait décorer une fonction"+\
                                   "génératrice (i.e qui utilise le mot-clé yield)")
            def decorated(*args, **kwargs) :
                entry = _GeneratorEntryType(args, kwargs, self.hargs, f.__qualname__)
                self.debugspace.history._add_call(entry, self.tags)
                self.debugspace._print_open(entry)

                yield from self.exec_iter(f, args, kwargs, entry)

                self.debugspace._print_close(entry)

            tracked = _TrackedCallableType(f,\
                                           decorated,\
                                           self.debugspace._config.trackers)
            self.debugspace._TRACKED.append(tracked)
            return tracked


    _TrackerType.__name__ = name
    return _TrackerType


# Les décorateurs DebugSpace.trackfunc(...) sont des objets de type _FunctionTracker
_FunctionTracker:type = tracker_type_builder('_FunctionTracker',\
                                             _TrackedFunction,\
                                             _CallEntry,\
                                             _GeneratorEntry)

# Les décorateurs DebugSpace.trackmethod(...) sont des objets de type _MethodTracker
_MethodTracker:type = tracker_type_builder('_MethodTracker',\
                                           _TrackedSelfMethod,\
                                           _SelfCallEntry,\
                                           _SelfGeneratorEntry)

# Les décorateurs DebugSpace.trackclassmethod(...) sont des instances de _ClassMethodTracker
_ClassMethodTracker:type = tracker_type_builder('_ClassMethodTracker',\
                                                _TrackedClsMethod,\
                                                _ClsCallEntry,\
                                                _ClsGeneratorEntry)




#--- user tools
def dbg_outputs_colors(disable:bool=False, reset:bool=False, **color_codes:str) :
    """Modifie la coloration des messages de debugage (la modification est
    appliquée à tous les espaces de debugage)

    Arguments
    -------------------------
    On considère dbg un espace de debugage

    disable : bool (False par défaut)
        True => désactive la coloration des messages de debugage

    reset : bool (False par défaut)
        True => reactive la coloration par défaut des message de debugage

    symbol : str (optional)
        Couleur du symbole précédant les messages de debugage générés par les
        décorateurs @dbg.trackfunc(...), @dbg.trackmethod(...),
        dbg.trackclassmethod(...) et @dbg.trackstaticmethod(...)

    arrow : str (optional)
        Couleur de la flèche qui précède les valeurs de retour des fonctions ou
        méthodes et de la flèche qui suit les valeurs envoyées aux généreteurs
        via leur méthode .send()

    error : str (optional)
        Couleur des erreurs

    undef : str (optional)
        Couleur des noms génériques comme <self> ou <object>

    time : str (optional)
        Couleur du texte indiquant la durée d'execution

    generator : str (optional)
        Couleur des noms des générateurs

    dbreak : str (optional)
        Couleur des messages précédant et suivant la mise pause du script via
        l'outil dbg.dbreak(...)

    regular : str (optional)
        Couleur des messages non-colorisés
    """
    global colors
    if disable :
        null = ''
        colors = ColorPalette(null, null, null, null, null, null, null, null)
    elif reset :
        colors = ColorPalette()
    else :
        params = dataclasses.asdict(colors)
        params.update(color_codes)
        colors = ColorPalette(**params)



class DebugSpace :
    """Implémente des espaces de debugage. Ce sont des ensembles d'outils
    permettant de faciliter les sessions de debugage de programmes complexes.
    Afin d'utiliser les outils de debugage de ce module, il faut créer un
    espace de debugage au début du script :
        import debug
        debug.dbg_outputs_colors(...) # configure la coloration des messages de
                                      # debugage (optionel)
                                      # voir help(dbg_outputs_colors)
        dbg = debug.DebugSpace(...) # créé un espace de debugage dbg
        dbg.configure(...) # modifie la configuration de dbg (optionel)
                           # voir help(DebugSpace.configure)

    Les outils de debugage sont alors accessibles dans la suite du script en
    tant qu'attributs de l'espace dbg.
    Les outils principaux :
        - dbg.dprint       # génerer des messages de debugage
        - dbg.dbreak       # mettre en pause l'execution du script
        - dbg.hiddenprint  # neutraliser temporairement l'affichage de texte
                             dans la console
    Les traqueurs :
        - dbg.trackfunc          # suivre l'execution d'une fonction
        - dbg.trackmethod        # suivre l'execution d'une méthode d'instance
        - dbg.trackclassmethod   # suivre l'execution d'une méthode de classe
        - dbg.trackstaticmethod  # suivre l'execution d'une méthode statique

    On peut ensuite étudier plus en détail l'execution du script une fois
    celle-ci terminée en consultant l'historique de debugage :
        - dbg.history  # permet d'acceder à l'historique de debugage associé à
                         l'espace dbg (voir help(DebugSpace.history))

    Pour faciliter leur lecture, les messages de debugage affichés dans la
    console sont par défaut colorés. Il est possible de modifier la coloration
    ou de la desactiver avec la fonction debug.dbg_outputs_colors


    Paramètres (aucuns paramètres positionels)
    -------------------------
    dbg = debug.DebugSpace(name=..., trackers=..., print_msg=...,\\
                                call_history=..., msg_history=...)

    name : str (optional)
        Nom de l'espace de debugage. Il s'affiche lorsque des messages de
        debugages sont générés avec la fonction dbg.dprint

    symbol : str (optional)
        Symbole affiché devant tous les messages de debugages générés par les
        décorateurs @dbg.trackfunc(...), @dbg.trackmethod(...),
        dbg.trackclassmethod(...) et @dbg.trackstaticmethod(...)

    trackers : bool (True par défaut)
        True <=> Les décorateurs @dbg.trackfunc(...), @dbg.trackmethod(...),
        dbg.trackclassmethod(...) et @dbg.trackstaticmethod(...) sont actifs

    print_msg : bool (True par défaut)
        True <=> Les messages de debugage s'affichent immediatement dans la
        console aux moments où ils sont générés lors de l'execution du
        programme

    msg_history : bool (False par défaut)
        True <=> Les messages de debugage sont enregistrés dans l'historique
        de debugage qui peut ensuite être consulté après l'execution du
        programme

    Ces paramètres peuvent être modifiés après l'instanciation de dbg avec la
    commande dbg.configure(...) (Voir help(DebugSpace.configure))


    Voir Aussi
    -------------------------
    help(DebugSpace.dprint)            # génerer des messages de debugage
    help(DebugSpace.dbreak)            # mettre en pause l'execution du script
    help(DebugSpace.hiddenprint)       # neutraliser temporairement l'affichage
                                         de texte dans la console

    help(DebugSpace.trackfunc)         # suivre l'execution d'une fonction
    help(DebugSpace.trackmethod)       # suivre l'execution d'une méthode d'instance
    help(DebugSpace.trackclassmethod)  # suivre l'execution d'une méthode de classe
    help(DebugSpace.trackstaticmethod) # suivre l'execution d'une méthode statique
    help(DebugSpace.history)           # acceder à l'historique de debugage

    help(DebugSpace.disable)           # désactiver les outils de debugage
    help(DebugSpace.enable)            # réactiver les outils de debugage
    help(DebugSpace.configure)         # reconfigurer l'espace de debugage
    help(DebugSpace.resetconfig)       # réinitialiser la configuration de
                                         l'espace de debugage
    """
    @property
    def symbol(self) :
        return _symbol_color(self._symbol)

    @property
    def _generator_symbol(self) :
        return _symbol_color('~~')

    @dataclasses.dataclass
    class _DbgSpaceParameters :
        name : str = 'debug print'
        symbol : str = '## '
        trackers : bool = True
        print_msg : bool = True
        msg_history : bool = False
        break_exec : bool = True

    def __init__(self, **kwargs) :
        self._level = 0 # niveau d'appel
        self.history = _DebugHistory() # historique de debugage
        self._TRACKED = [] # liste des fonctions ou méthodes trackées
        self._is_hiding_prints = None # flag qui vaut True quand hiddenprints est utilisé
        self._config = self._DbgSpaceParameters() # configuration actuelle
        self.configure(**kwargs)
        self._init_config = self._config # configuration initiale

    history = _DebugHistory # permet de rediriger l'aide help(DebugSpace.history)


    def configure(self, *, name=None, symbol=None, trackers=None, print_msg=None,\
                  msg_history=None, break_exec=None) :
        """dbg.configure() reconfigure l'espace de debugage dbg

        Paramètres (aucuns paramètres positionels)
        -------------------------
        même signature que pour instancier un espace de debugage
        (Voir help(DebugSpace))
        """
        if name is None :
            name = self._config.name
        elif not isinstance(name, str) :
            raise DebugError('name doit être une chaine de caractères')
        self.name = name

        if symbol is None :
            symbol = self._config.symbol
        elif not isinstance(symbol, str) :
            raise DebugError('symbol doit être une chaine de caractère')
        else :
            symbol = symbol.strip() + ' '
        self._symbol = symbol

        if trackers is None :
            trackers = self._config.trackers
        for tracked in self._TRACKED :
            tracked._setcallmode(trackers)

        if print_msg is None :
            print_msg = self._config.print_msg
        if print_msg :
            self._display_dbg_msg = self.__display_dbg_msg
            self._print_call = self.__print_call
            self._print_return = self.__print_return
            self._print_send = self.__print_send
            self._print_yield = self.__print_yield
            self._print_open = self.__print_open
            self._print_close = self.__print_close
        else :
            self._display_dbg_msg = _pass_func
            self._print_call = _pass_func
            self._print_return = _pass_func
            self._print_send = _pass_func
            self._print_yield = _pass_func
            self._print_open = _pass_func
            self._print_close = _pass_func

        if msg_history is None :
            msg_history = self._config.msg_history
        if msg_history :
            self._msg_history_add = self.__msg_history_add
        else :
            self._msg_history_add = _pass_func

        if break_exec is None :
            break_exec = self._config.break_exec
        if break_exec :
            self._break = self.__break
        else :
            self._break = _pass_func

        # sauvegarde de la configuration actuelle
        self._config = self._DbgSpaceParameters(name, symbol, trackers, print_msg,\
                                                msg_history, break_exec)


    def __repr__(self) :
        return repr(self._config)


    # --- msg history
    def __msg_history_add(self, msg:str) :
        self.history._add_message(msg)


    # --- outputs methods
    def __display_dbg_msg(self, *args, sep=' ', **kwargs) :
        header = f"|{self.name}| "
        lines = sep.join(map(str, args)).splitlines()
        print(
            _symbol_color(header),
            ('\n'+len(header)*' ').join(lines),
            sep='',
            **kwargs
            )

    def __print_call(self, entry:_CallEntry) :
        msg = f"{self.symbol*entry.call_level}{entry._call_repr()}"
        print(msg)
        self._msg_history_add(msg)

    def __print_return(self, entry:_CallEntry) :
        msg = f"{self.symbol*entry.call_level}{entry._return_repr()}"
        print(msg)
        self._msg_history_add(msg)

    def __print_open(self, entry:_GeneratorEntry) :
        msg = f"{self._generator_symbol} {entry.name} started"
        print(msg)
        self._msg_history_add(msg)

    def __print_send(self, entry:_GeneratorEntry) :
        msg = f'{self._generator_symbol} {entry._send_repr()}'
        print(msg)
        self._msg_history_add(msg)

    def __print_yield(self, entry:_GeneratorEntry) :
        msg = f'{self._generator_symbol} {entry._yield_repr()}'
        print(msg)
        self._msg_history_add(msg)

    def __print_close(self, entry:_GeneratorEntry) :
        msg = f"{self._generator_symbol} {entry.name} exhausted"
        print(msg)
        self._msg_history_add(msg)


    # --- breaks
    def __break(self, args:tuple, msg:str, condition:bool) -> bool :
        if condition :
            if self._is_hiding_prints :
                sys.stdout, nullfile = self._is_hiding_prints
            else :
                nullfile = None

            print(f'\n-------\n{_break_color("|break|")}\n'+\
                  '\n'.join(f'{_ObjRepr(obj)}' for obj in args))
            if msg :
                print(msg)

            command = input('>>> ')
            disable = False
            while command != 'exit' :
                if command in ('help', 'h') :
                    print("commandes dbreak :\n"+\
                          " h[elp] : affiche ce message d'aide\n"
                          " c[ontinue] : continue l'execution jusqu'au prochain "+\
                          "dbreak(...)\n"+\
                          " d[isable] : continue l'execution en desactivant "+\
                          "dbreak(...)\n"+\
                          " q[uit] : stoppe l'execution avec sys.exit()")
                    command = input('>>> ')
                elif command in ('d', 'disable') :
                    disable = True
                    print(_break_color(f'{_break_color("|fin du break|")} : '+\
                                       'dbreak(...) desactivé\n-------\n'))
                    break
                elif command in ('q', 'quit') :
                    sys.exit()
                else :
                    print(_break_color(f'{_break_color("|fin du break|")}\n-------\n'))
                    break

            if nullfile :
                sys.stdout = nullfile
            return disable


    # --- user tools
    def disable(self) : # desactive tous les paramètres
        """dbg.disable() désactive les traqueurs et l'outil dbg.dprint()

        Voir aussi
        -------------------------
        help(DebugSpace.dprint)      # génerer un message de debugage
        help(DebugSpace.trackfunc)   # tracker une fonction
        help(DebugSpace.trackmethod) # tracker une méthode
        """
        self.configure(trackers=False, print_msg=False, msg_history=False)


    def enable(self) : # active tous les paramètres
        """dbg.enable() active les traqueurs et l'outil dbg.dprint()

        Voir aussi
        -------------------------
        help(DebugSpace.dprint)      # génerer un message de debugage
        help(DebugSpace.trackfunc)   # tracker une fonction
        help(DebugSpace.trackmethod) # tracker une méthode
        """
        self.configure(trackers=True, print_msg=True, msg_history=True)


    def resetconfig(self) : # remet la configuration initiale des paramètres
        """dbg.resetconfig() réinitialise les paramètres de l'espace de
        debugage dbg

        Voir aussi
        -------------------------
        help(DebugSpace.configure)
        """
        self.configure(**dataclasses.asdict(self._init_config))


    def dbreak(self, *args:Any, msg:str='', condition:bool=True) :
        """Version simplifiée de la fonction native breakpoint

        On considère que dbg est un espace de debugage
        dbg.dbreak(...) met en pause l'execution du script jusqu'à ce que
        l'utilisateur la relance

        Arguments
        -------------------------
        *args : Any
            Objets à afficher lors de la pause

        msg : str (optional)
            Message à afficher lors de la pause

        condition : bool (True par défaut)
            Le script ne se met en pause que si la condition vaut True
        """
        if condition and self._break(args, msg, condition) :
            self._break = _pass_func


    def dprint(self, msg='', *args, sep:str=' ', end:str='\n', **kwargs) :
        """On considère que dbg est un espace de debugage
        dbg.dprint() génère un message de debugage et l'affiche dans la console
        si l'option print_msg de dbg a été activée

        Arguments
        -------------------------
        Même signature que le fonction native print()

        Voir aussi
        -------------------------
        help(DebugSpace)                   # créer l'espace de debugage
        help(DebugSpace.configure)         # reconfigurer l'espace de debugage
        help(DebugSpace.dbreak)            # mettre en pause l'execution du script
        help(DebugSpace.hiddenprints)      # ne pas afficher de texte dans la console
        help(DebugSpace.trackfunc)         # suivre l'execution d'une fonction
        help(DebugSpace.trackmethod)       # suivre l'execution d'une méthode d'instance
        help(DebugSpace.trackclassmethod)  # suivre l'execution d'une méthode de classe
        help(DebugSpace.trackstaticmethod) # suivre l'execution d'une méthode statique
        """
        self._display_dbg_msg(msg, *args, sep=sep, end=end, **kwargs)
        self._msg_history_add(str(msg) + sep.join(map(str, args)))


    def hiddenprints(self, f) :
        """On considère que dbg est un espace de debugage.

        Une fonction ou méthode décorrée par @dbg.hiddenprints n'affiche aucun
        texte dans la console lors de son exécution.
        """
        def decorated(*args, **kwargs) :
            # desactive print
            nullfile = open(devnull, 'w')
            originalfile = sys.stdout
            self._is_hiding_prints = [originalfile, nullfile]
            sys.stdout = nullfile
            # execute la fonction
            result = f(*args, **kwargs)
            # reactive print et renvoi le resultat
            sys.stdout = originalfile
            nullfile.close()
            self._is_hiding_prints = None
            return result
        return decorated

    # TODO : mettre une option break_condition dans les traqueurs
    # TODO : ameliorer le système de chronometrage dans les cas des appels imbriqués et des mises en pause du script
    def trackfunc(self, *tags:str, hidden_args:Iterable[Union[int, str]]=None,\
                  chrono:bool=False, yieldfunc:bool=False) :
        """On considère que dbg est un espace de debugage.

        Lorsqu'une fonction décorée par @dbg.trackfunc(...) est appellée :
         - deux messages de debugages sont générés :
            - avant l'execution : un message qui contient le nom de la fonction
             et les arguments qui lui sont passés (sauf les paramètres speciaux
             self ou cls)
            - après l'execution (si celle-ci n'a pas echouée) : un message qui
             contient la valeur que la fonction a renvoyée
         - l'execution de la fonction est enregistrée dans l'historique de
          debugage dbg.history


        Utilisation
        -------------------------
        @dbg.trackfunc(*tags, chrono) doit seulement être utilisé pour suivre
        les executions de fonctions

        exemple :
        dbg = DebugSpace(...) # crée l'espace de debugage : voir help(DebugSpace)

        @dbg.trackfunc(...) # suit l'execution de la fonction foo
        def foo(...) :
            ...


        Paramètres
        -------------------------
        *tags : str (optionals)
            Liste des tags auxquels vont être assosiées les entrées
            correspondants aux executions de la fonction décorée dans
            l'historique de debugage (si celui-ci a été activé)

        hidden_args : iterable of (int or str)
            Contient les indices ou les noms des attributs positionels ou
            à mot clé dont la représentation complète ne doit pas être affichée
            dans les messages de debugage

        chrono : bool (False par défaut)
            True <=> Les executions de la méthode décorée seront chronometrées
            et les temps d'execution seront enregistrés dans l'historique de
            debugage (si celui_ci a été activé)

        yieldfunc : bool (False par défaut)
            True <=> La fonction décorée est une fonction genératrice et les
            genérateurs qu'elle crée seront traqués


        Voir aussi
        -------------------------
        help(DebugSpace)                   # créer l'espace de debugage
        help(DebugSpace.configure)         # reconfigurer l'espace de debugage
        help(DebugSpace.history)           # acceder à l'historique de debugage
        help(DebugSpace.dprint)            # génerer un message de debugage
        help(DebugSpace.trackmethod)       # suivre l'execution d'une méthode d'instance
        help(DebugSpace.trackclassmethod)  # suivre l'execution d'une méthode de classe
        help(DebugSpace.trackstaticmethod) # suivre l'execution d'une méthode statique
        """
        if any(not isinstance(tag, str) for tag in tags) :
            raise TrackerError('Les tags doivent être des chaines de caractères')
        if hidden_args :
            hidden_args = set(hidden_args)
        else :
            hidden_args = {}
        return _FunctionTracker(self, tags, hidden_args, chrono, yieldfunc)


    def trackmethod(self, *tags:str, hidden_args:Iterable[Union[int, str]]=None,\
                    chrono:bool=False, yieldfunc:bool=False) :
        """On considère que dbg est un espace de debugage.

        Lorsqu'une méthode d'instance décorée par @dbg.trackmethod(...)
        est appellée :
         - deux messages de debugages sont générés :
            - avant l'execution : un message qui contient le nom de la méthode
             et les arguments qui lui sont passés (sauf les paramètres speciaux
             self ou cls)
            - après l'execution (si celle-ci n'a pas echouée) : un message qui
             contient le nom de la méthode et la valeur qu'elle a renvoyé
         - l'execution de la méthode est enregistrée dans l'historique de
          debugage dbg.history


        Utilisation
        -------------------------
        @dbg.trackmethod(...) doit seulement être utilisée pour suivre les
        executions de méthodes d'instance

        exemple :
        dbg = DebugSpace(...) # crée l'espace de debugage : voir help(DebugSpace)

        class Foo :
            @dbg.trackmethod(...) # suit l'execution de la méthode d'instance bar
            def bar(self, ...) :
                ...


        Paramètres
        -------------------------
        *tags : str (optionals)
            Liste des tags auxquels vont être assosiées les entrées
            correspondants aux executions de la méthode décorée dans
            l'historique de debugage (si celui-ci a été activé)

        hidden_args : iterable of (int or str)
            Contient les indices ou les noms des attributs positionels ou
            à mot clé dont la représentation complète ne doit pas être affichée
            dans les messages de debugage

        chrono : bool (False par défaut)
            True <=> Les executions de la méthode décorée seront chronometrées
            et les temps d'execution seront enregistrés dans l'historique de
            debugage (si celui_ci a été activé)

        yieldfunc : bool (False par défaut)
            True <=> La méthode décorée est une fonction genératrice et les
            genérateurs qu'elle crée seront traqués


        Voir aussi
        -------------------------
        help(DebugSpace)                   # créer l'espace de debugage
        help(DebugSpace.configure)         # reconfigurer l'espace de debugage
        help(DebugSpace.history)           # acceder à l'historique de debugage
        help(DebugSpace.dprint)            # génerer un message de debugage
        help(DebugSpace.trackfunc)         # suivre l'execution d'une fonction
        help(DebugSpace.trackclassmethod)  # suivre l'execution d'une méthode de classe
        help(DebugSpace.trackstaticmethod) # suivre l'execution d'une méthode statique
        """
        if any(not isinstance(tag, str) for tag in tags) :
            raise TrackerError('Les tags doivent être des chaines de caractères')
        if hidden_args :
            hidden_args = set(hidden_args)
        else :
            hidden_args = {}
        return _MethodTracker(self, tags, hidden_args, chrono, yieldfunc)


    def trackclassmethod(self, *tags:str, hidden_args:Iterable[Union[int, str]]=None,\
                         chrono:bool=False, yieldfunc:bool=False) :
        """On considère que dbg est un espace de debugage.

        Lorsqu'une méthode de classe décorée par @dbg.trackclassmethod(...)
        est appellée :
         - deux messages de debugages sont générés :
            - avant l'execution : un message qui contient le nom de la méthode
             et les arguments qui lui sont passés (sauf les paramètres speciaux
             self ou cls)
            - après l'execution (si celle-ci n'a pas echouée) : un message qui
             contient le nom de la méthode et la valeur qu'elle a renvoyé
         - l'execution de la méthode est enregistrée dans l'historique de
          debugage dbg.history


        Utilisation
        -------------------------
        @dbg.trackclassmethod(...) doit seulement être utilisée pour suivre les
        executions de méthodes de classe

        exemple :
        dbg = DebugSpace(...) # crée l'espace de debugage : voir help(DebugSpace)

        class Foo :
            @classmethod
            @dbg.tracclasskmethod(...) # suit l'execution de la méthode de classe bar
            def bar(cls, ...) :
                ...


        Paramètres
        -------------------------
        *tags : str (optionals)
            Liste des tags auxquels vont être assosiées les entrées
            correspondants aux executions de la méthode décorée dans
            l'historique de debugage (si celui-ci a été activé)

        hidden_args : iterable of (int or str)
            Contient les indices ou les noms des attributs positionels ou
            à mot clé dont la représentation complète ne doit pas être affichée
            dans les messages de debugage

        chrono : bool (False par défaut)
            True <=> Les executions de la méthode décorée seront chronometrées
            et les temps d'execution seront enregistrés dans l'historique de
            debugage (si celui_ci a été activé)

        yieldfunc : bool (False par défaut)
            True <=> La méthode décorée est une fonction genératrice et les
            genérateurs qu'elle crée seront traqués


        Voir aussi
        -------------------------
        help(DebugSpace)                   # créer l'espace de debugage
        help(DebugSpace.configure)         # reconfigurer l'espace de debugage
        help(DebugSpace.history)           # acceder à l'historique de debugage
        help(DebugSpace.dprint)            # génerer un message de debugage
        help(DebugSpace.trackfunc)         # suivre l'execution d'une fonction
        help(DebugSpace.trackclassmethod)  # suivre l'execution d'une méthode de classe
        help(DebugSpace.trackstaticmethod) # suivre l'execution d'une méthode statique
        """
        if any(not isinstance(tag, str) for tag in tags) :
            raise TrackerError('Les tags doivent être des chaines de caractères')
        if hidden_args :
            hidden_args = set(hidden_args)
        else :
            hidden_args = {}
        return _ClassMethodTracker(self, tags, hidden_args, chrono, yieldfunc)


    def trackstaticmethod(self, *tags:str, hidden_args:Iterable[Union[int, str]]=None,\
                          chrono:bool=False, yieldfunc:bool=False) :
        """On considère que dbg est un espace de debugage.

        Lorsqu'une méthode statique décorée par @dbg.trackstaticmethod(...)
        est appellée :
         - deux messages de debugages sont générés :
            - avant l'execution : un message qui contient le nom de la fonction
             et les arguments qui lui sont passés (sauf les paramètres speciaux
             self ou cls)
            - après l'execution (si celle-ci n'a pas echouée) : un message qui
             contient la valeur que la fonction a renvoyée
         - l'execution de la fonction est enregistrée dans l'historique de
          debugage dbg.history


        Utilisation
        -------------------------
        @dbg.trackstaticmethod(...) doit seulement être utilisé pour suivre les
        executions de méthodes statiques

        exemple :
        dbg = DebugSpace(...) # crée l'espace de debugage : voir help(DebugSpace)

        class Foo :
            @staticmethod
            @dbg.trackstaticmethod(...) # suit l'execution de la méthode statique bar
            def bar(...) :
                ...


        Paramètres
        -------------------------
        *tags : str (optionals)
            Liste des tags auxquels vont être assosiées les entrées
            correspondants aux executions de la fonction décorée dans
            l'historique de debugage (si celui-ci a été activé)

        hidden_args : iterable of (int or str)
            Contient les indices ou les noms des attributs positionels ou
            à mot clé dont la représentation complète ne doit pas être affichée
            dans les messages de debugage

        chrono : bool (False par défaut)
            True <=> Les executions de la méthode décorée seront chronometrées
            et les temps d'execution seront enregistrés dans l'historique de
            debugage (si celui_ci a été activé)

        yieldfunc : bool (False par défaut)
            True <=> La méthode décorée est une fonction genératrice et les
            genérateurs qu'elle crée seront traqués


        Voir aussi
        -------------------------
        help(DebugSpace)                   # créer l'espace de debugage
        help(DebugSpace.configure)         # reconfigurer l'espace de debugage
        help(DebugSpace.history)           # acceder à l'historique de debugage
        help(DebugSpace.dprint)            # génerer un message de debugage
        help(DebugSpace.trackmethod)       # suivre l'execution d'une méthode d'instance
        help(DebugSpace.trackclassmethod)  # suivre l'execution d'une méthode de classe
        help(DebugSpace.trackstaticmethod) # suivre l'execution d'une méthode statique
        """
        if any(not isinstance(tag, str) for tag in tags) :
            raise TrackerError('Les tags doivent être des chaines de caractères')
        if hidden_args :
            hidden_args = set(hidden_args)
        else :
            hidden_args = {}
        return _FunctionTracker(self, tags, hidden_args, chrono, yieldfunc)



# --- exemples
if __name__ == '__main__' :
    dbg = DebugSpace(name='debug example')

    @dbg.trackfunc()
    def function(*args, **kwargs) :
        """test documentation"""
        pass

    @dbg.trackfunc(chrono=True)
    def error(*args, **kwargs) :
        raise Exception

    @dbg.trackfunc('tag_example', chrono=True, hidden_args=[0])
    def div(a, b) :
        return a / b

    @dbg.trackfunc('matrix', chrono=True)
    def matmul(*matrices) :
        if len(matrices) == 0 :
            return 1
        if len(matrices) == 1 :
            return matrices[0]
        return matrices[0] * matmul(*matrices[1:])

    @dbg.trackfunc('tag_example', chrono=True)
    def expensiveroutine(*args, **kwargs) :
        lst = list(range(10000000))
        lst.sort(reverse=True)

    @dbg.trackfunc(chrono = True)
    def factorial(n:int) :
        if n == 0 :
            return 1
        return n*factorial(n-1)

    @dbg.trackfunc('test_generator', chrono=True, yieldfunc=True)
    def gener(n:int) :
        y = n
        for i in range(10) :
            x = yield y
            if x :
               y += x

    @dbg.trackfunc('test_generator', chrono=True, yieldfunc=True)
    def error_gener(n) :
        for i in range(n) :
            yield i
        raise ValueError('test')

    class Too :
        @dbg.trackmethod('tag_example', chrono=True, hidden_args=[2])
        def foo(self, *args, **kwargs) :
            return args, kwargs

        @classmethod
        @dbg.trackclassmethod('other_tag', chrono=True)
        def bar(cls, *args, **kwargs) :
            return cls, args, kwargs

        @staticmethod
        @dbg.trackstaticmethod('other_tag', chrono=True)
        def boo(*args, **kwargs) :
            return args, kwargs

        @dbg.trackmethod()
        def call_another(self) :
            return self.foo(1, 2, pos=3)

        @dbg.trackmethod(yieldfunc=True)
        def yieldmethod(self, n) :
            for i in range(n) :
                yield i

    t = Too()
    t.foo()

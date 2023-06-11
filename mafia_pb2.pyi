from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
ROLE_DETECTIVE: Role
ROLE_MAFIA: Role
ROLE_UNSPECIFIED: Role
ROLE_VILLAGER: Role

class CheckRequest(_message.Message):
    __slots__ = ["player_id", "token"]
    PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    player_id: int
    token: str
    def __init__(self, token: _Optional[str] = ..., player_id: _Optional[int] = ...) -> None: ...

class CheckResponse(_message.Message):
    __slots__ = ["mafias"]
    MAFIAS_FIELD_NUMBER: _ClassVar[int]
    mafias: _containers.RepeatedCompositeFieldContainer[Player]
    def __init__(self, mafias: _Optional[_Iterable[_Union[Player, _Mapping]]] = ...) -> None: ...

class ConnectRequest(_message.Message):
    __slots__ = ["name"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class ConnectResponse(_message.Message):
    __slots__ = ["token"]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    token: str
    def __init__(self, token: _Optional[str] = ...) -> None: ...

class CreateGameRequest(_message.Message):
    __slots__ = ["required_players_cnt", "token"]
    REQUIRED_PLAYERS_CNT_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    required_players_cnt: int
    token: str
    def __init__(self, token: _Optional[str] = ..., required_players_cnt: _Optional[int] = ...) -> None: ...

class CreateGameResponse(_message.Message):
    __slots__ = ["code"]
    CODE_FIELD_NUMBER: _ClassVar[int]
    code: str
    def __init__(self, code: _Optional[str] = ...) -> None: ...

class EndDayRequest(_message.Message):
    __slots__ = ["token"]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    token: str
    def __init__(self, token: _Optional[str] = ...) -> None: ...

class EndDayResponse(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class GameProcessRequest(_message.Message):
    __slots__ = ["token"]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    token: str
    def __init__(self, token: _Optional[str] = ...) -> None: ...

class GameProcessResponse(_message.Message):
    __slots__ = ["day", "end", "night"]
    class EndGame(_message.Message):
        __slots__ = ["winner"]
        WINNER_FIELD_NUMBER: _ClassVar[int]
        winner: Role
        def __init__(self, winner: _Optional[_Union[Role, str]] = ...) -> None: ...
    class StartDay(_message.Message):
        __slots__ = ["detective", "is_alive", "mafias", "players"]
        DETECTIVE_FIELD_NUMBER: _ClassVar[int]
        IS_ALIVE_FIELD_NUMBER: _ClassVar[int]
        MAFIAS_FIELD_NUMBER: _ClassVar[int]
        PLAYERS_FIELD_NUMBER: _ClassVar[int]
        detective: Player
        is_alive: bool
        mafias: _containers.RepeatedCompositeFieldContainer[Player]
        players: _containers.RepeatedCompositeFieldContainer[Player]
        def __init__(self, is_alive: bool = ..., players: _Optional[_Iterable[_Union[Player, _Mapping]]] = ..., mafias: _Optional[_Iterable[_Union[Player, _Mapping]]] = ..., detective: _Optional[_Union[Player, _Mapping]] = ...) -> None: ...
    class StartNight(_message.Message):
        __slots__ = ["is_alive", "mafias", "players", "role"]
        IS_ALIVE_FIELD_NUMBER: _ClassVar[int]
        MAFIAS_FIELD_NUMBER: _ClassVar[int]
        PLAYERS_FIELD_NUMBER: _ClassVar[int]
        ROLE_FIELD_NUMBER: _ClassVar[int]
        is_alive: bool
        mafias: _containers.RepeatedCompositeFieldContainer[Player]
        players: _containers.RepeatedCompositeFieldContainer[Player]
        role: Role
        def __init__(self, is_alive: bool = ..., role: _Optional[_Union[Role, str]] = ..., players: _Optional[_Iterable[_Union[Player, _Mapping]]] = ..., mafias: _Optional[_Iterable[_Union[Player, _Mapping]]] = ...) -> None: ...
    DAY_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    NIGHT_FIELD_NUMBER: _ClassVar[int]
    day: GameProcessResponse.StartDay
    end: GameProcessResponse.EndGame
    night: GameProcessResponse.StartNight
    def __init__(self, day: _Optional[_Union[GameProcessResponse.StartDay, _Mapping]] = ..., night: _Optional[_Union[GameProcessResponse.StartNight, _Mapping]] = ..., end: _Optional[_Union[GameProcessResponse.EndGame, _Mapping]] = ...) -> None: ...

class GetRoleRequest(_message.Message):
    __slots__ = ["token"]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    token: str
    def __init__(self, token: _Optional[str] = ...) -> None: ...

class GetRoleResponse(_message.Message):
    __slots__ = ["role"]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    role: Role
    def __init__(self, role: _Optional[_Union[Role, str]] = ...) -> None: ...

class JoinGameRequest(_message.Message):
    __slots__ = ["code", "token"]
    CODE_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    code: str
    token: str
    def __init__(self, token: _Optional[str] = ..., code: _Optional[str] = ...) -> None: ...

class JoinGameResponse(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ListPlayersRequest(_message.Message):
    __slots__ = ["token"]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    token: str
    def __init__(self, token: _Optional[str] = ...) -> None: ...

class ListPlayersResponse(_message.Message):
    __slots__ = ["players", "required_players_cnt"]
    PLAYERS_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_PLAYERS_CNT_FIELD_NUMBER: _ClassVar[int]
    players: _containers.RepeatedCompositeFieldContainer[Player]
    required_players_cnt: int
    def __init__(self, required_players_cnt: _Optional[int] = ..., players: _Optional[_Iterable[_Union[Player, _Mapping]]] = ...) -> None: ...

class Player(_message.Message):
    __slots__ = ["id", "name"]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    def __init__(self, name: _Optional[str] = ..., id: _Optional[int] = ...) -> None: ...

class PublishRequest(_message.Message):
    __slots__ = ["decision", "token"]
    DECISION_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    decision: bool
    token: str
    def __init__(self, token: _Optional[str] = ..., decision: bool = ...) -> None: ...

class PublishResponse(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class VoteDayRequest(_message.Message):
    __slots__ = ["player_id", "token"]
    PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    player_id: int
    token: str
    def __init__(self, token: _Optional[str] = ..., player_id: _Optional[int] = ...) -> None: ...

class VoteDayResponse(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class VoteNightRequest(_message.Message):
    __slots__ = ["player_id", "token"]
    PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    player_id: int
    token: str
    def __init__(self, token: _Optional[str] = ..., player_id: _Optional[int] = ...) -> None: ...

class VoteNightResponse(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class Role(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

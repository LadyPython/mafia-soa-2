import logging
import os
import string
import typing
import uuid

import grpc

import mafia_pb2
import mafia_pb2_grpc

import asyncio
import random


class PlayerInfo:
    def __init__(self):
        self.role: mafia_pb2.Role = mafia_pb2.ROLE_UNSPECIFIED
        self.is_alive = True

    def is_mafia(self):
        return self.role == mafia_pb2.ROLE_MAFIA

    def is_detective(self):
        return self.role == mafia_pb2.ROLE_DETECTIVE


class Game:
    next_id = 1

    def __init__(self, required_players_cnt: int):
        self.required_players_cnt = required_players_cnt

        self.player_id_to_player_info: dict[int, PlayerInfo] = dict()

        self.votes: dict[int, int] = dict()
        self.event_started: asyncio.Event = asyncio.Event()
        self.event_killed: asyncio.Event = asyncio.Event()
        self.event_checked: asyncio.Event = asyncio.Event()
        self.checked_decision: bool | None = None
        self.checked_ids: list[int] = []
        self.started_cnt = 0

        self.id: int = Game.next_id
        logging.info(f"New Game({required_players_cnt}, id={Game.next_id})")
        Game.next_id += 1

    def assign_roles(self):
        mafia_cnt = self.required_players_cnt // 4
        roles = [mafia_pb2.ROLE_DETECTIVE] + [mafia_pb2.ROLE_MAFIA] * mafia_cnt + \
                [mafia_pb2.ROLE_VILLAGER] * (self.required_players_cnt - mafia_cnt - 1)
        random.shuffle(roles)

        for id, role in zip(self.player_id_to_player_info.keys(), roles):
            self.player_id_to_player_info[id].role = role

        logging.info(f"Roles assigned")

    def add_player(self, player_id: int):
        if len(self.player_id_to_player_info) == self.required_players_cnt:
            raise Exception(f'Game {self.id} is full')

        self.player_id_to_player_info[player_id] = PlayerInfo()
        if len(self.player_id_to_player_info) == self.required_players_cnt:
            self.assign_roles()

        logging.info(f"{player_id} added")

    def get_alive_players_ids(self) -> set[int]:
        return set([player_id for player_id, player in self.player_id_to_player_info.items() if player.is_alive])

    def get_alive_mafias_ids(self) -> set[int]:
        return set([player_id for player_id, player in self.player_id_to_player_info.items() if
                    player.is_alive and player.is_mafia()])

    def get_alive_detective_id(self) -> int | None:
        for player_id, player in self.player_id_to_player_info.items():
            if player.is_alive and player.is_detective():
                return player_id
        return None

    def choose_and_kill_player(self, votes: list[int], candidates_ids: set[int]):
        chosen_id = max(candidates_ids, key=votes.count)

        self.player_id_to_player_info[chosen_id].is_alive = False
        self.event_killed.set()

        logging.info(f"{chosen_id} killed")

    def add_vote(self, player_id: int, candidate_id: int, voters_ids: set[int]):
        if player_id not in voters_ids:
            raise Exception(f'{player_id} is not voter.')

        if player_id in self.votes:
            raise Exception(f'{player_id} already voted.')

        alive_players_ids = self.get_alive_players_ids()
        if candidate_id not in alive_players_ids:
            raise Exception(f'{candidate_id} is not alive candidate.')

        self.votes[player_id] = candidate_id
        if len(self.votes) == len(voters_ids):
            self.choose_and_kill_player(list(self.votes.values()), alive_players_ids)
            self.votes = dict()

        logging.info(f"{player_id} -> {candidate_id} added")

    def add_day_vote(self, player_id: int, candidate_id: int):
        self.add_vote(player_id, candidate_id, self.get_alive_players_ids())

    def add_night_vote(self, player_id: int, candidate_id: int):
        self.add_vote(player_id, candidate_id, self.get_alive_mafias_ids())

    def get_player_role(self, player_id: int, candidate_id: int) -> mafia_pb2.Role:
        player_info = self.player_id_to_player_info[player_id]
        if not player_info.is_detective():
            raise Exception(f'{player_id} cannot check.')

        candidate_info = self.player_id_to_player_info[candidate_id]
        if candidate_info.is_mafia():
            self.checked_ids.append(candidate_id)
        return candidate_info.role

    def check(self, player_id: int, candidate_id: int):
        player_info = self.player_id_to_player_info[player_id]
        if not player_info.is_detective():
            raise Exception(f'{player_id} cannot check.')

        candidate_info = self.player_id_to_player_info[candidate_id]
        if candidate_info.is_mafia():
            self.checked_ids.append(candidate_id)

    def publish(self, player_id: int, decision: bool):
        player_info = self.player_id_to_player_info[player_id]
        if not player_info.is_detective():
            raise Exception(f'{player_id} cannot publish.')

        self.checked_decision = decision
        self.event_checked.set()

    def start(self):
        self.started_cnt += 1
        if self.started_cnt == self.required_players_cnt:
            self.event_started.set()

    def start_night(self):
        self.checked_decision = None
        self.event_killed.clear()
        if self.get_alive_detective_id() is not None:
            self.event_checked.clear()

    def start_day(self):
        self.event_killed.clear()

    def get_winner(self) -> mafia_pb2.Role:
        players = self.get_alive_players_ids()
        mafias = self.get_alive_mafias_ids()
        if not mafias:
            return mafia_pb2.ROLE_VILLAGER
        if 2 * len(mafias) >= len(players):
            return mafia_pb2.ROLE_MAFIA
        return None


def check(response):
    def wrapper(handler):
        async def wrapped(self, request, context):
            if request.token not in self.token_to_player:
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                context.set_details(f"Player {request.token} not registered")
                return response

            player = self.token_to_player[request.token]

            if player.id not in self.player_id_to_game_id:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Player {player.name}({player.id}) isn't playing any game")
                return response

            game_id = self.player_id_to_game_id[player.id]

            if game_id not in self.game_id_to_game:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"Game {game_id} is broken")
                return response

            game = self.game_id_to_game[game_id]
            return await handler(self, request, context, player, game)
        return wrapped
    return wrapper


class EService(mafia_pb2_grpc.MafiaServicer):
    player_next_id = 1

    def __init__(self):
        self.token_to_player: dict[str, mafia_pb2.Player] = dict()
        self.code_to_game: dict[str, Game] = dict()

        self.player_id_to_player: dict[int, mafia_pb2.Player] = dict()
        self.game_id_to_game: dict[int, Game] = dict()

        self.player_id_to_game_id: dict[int, int] = dict()

    async def Connect(self, request: mafia_pb2.ConnectRequest, context) -> mafia_pb2.ConnectResponse:
        player = mafia_pb2.Player(name=request.name, id=EService.player_next_id)
        EService.player_next_id += 1

        token = str(uuid.uuid4())
        self.token_to_player[token] = player
        self.player_id_to_player[player.id] = player

        logging.info(f"{player.name}({player.id}) ~ {token}")
        return mafia_pb2.ConnectResponse(token=token)

    async def CreateGame(self, request: mafia_pb2.CreateGameRequest, context) -> mafia_pb2.CreateGameResponse:
        if request.token not in self.token_to_player:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details(f"Token {request.token} is not registered")
            return mafia_pb2.CreateGameResponse()

        player = self.token_to_player[request.token]

        game = Game(request.required_players_cnt)

        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        self.code_to_game[code] = game
        self.game_id_to_game[game.id] = game

        game.add_player(player.id)
        self.player_id_to_game_id[player.id] = game.id

        logging.info(f"{player.name}({player.id}) !{code}({game.id})")
        return mafia_pb2.CreateGameResponse(code=code)

    async def JoinGame(self, request: mafia_pb2.JoinGameRequest, context) -> mafia_pb2.JoinGameResponse:
        if request.token not in self.token_to_player:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details(f"Player {request.token} not registered")
            return mafia_pb2.JoinGameResponse()

        player = self.token_to_player[request.token]

        if request.code not in self.code_to_game:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Game {request.code} not found")
            return mafia_pb2.JoinGameResponse()

        game = self.code_to_game[request.code]

        game.add_player(player.id)
        self.player_id_to_game_id[player.id] = game.id

        logging.info(f"{player.name}({player.id}) +{request.code}({game.id})")
        return mafia_pb2.JoinGameResponse()

    @check(mafia_pb2.ListPlayersResponse())
    async def ListPlayers(self, request: mafia_pb2.ListPlayersRequest, context, player, game) -> mafia_pb2.ListPlayersResponse:
        return mafia_pb2.ListPlayersResponse(required_players_cnt=game.required_players_cnt,
                                             players=[self.player_id_to_player[player_id] for player_id in
                                                      game.player_id_to_player_info.keys()])

    @check(mafia_pb2.GetRoleResponse())
    async def GetRole(self, request: mafia_pb2.GetRoleRequest, context, player, game) -> mafia_pb2.GetRoleResponse:
        role = game.player_id_to_player_info[player.id].role

        logging.info(f"{game.id}: {player.name}({player.id}) is {role}")
        return mafia_pb2.GetRoleResponse(role=role)

    @check(mafia_pb2.VoteDayResponse())
    async def VoteDay(self, request: mafia_pb2.VoteDayRequest, context, player, game) -> mafia_pb2.VoteDayResponse:
        game.add_day_vote(player.id, request.player_id)

        logging.info(f"{game.id}: {player.name}({player.id}) V {request.player_id}")
        return mafia_pb2.VoteDayResponse()

    @check(mafia_pb2.VoteNightResponse())
    async def VoteNight(self, request: mafia_pb2.VoteNightRequest, context, player, game) -> mafia_pb2.VoteNightResponse:
        game.add_night_vote(player.id, request.player_id)

        logging.info(f"{game.id}: {player.name}({player.id}) X {request.player_id}")
        return mafia_pb2.VoteNightResponse()

    @check(mafia_pb2.CheckResponse())
    async def Check(self, request: mafia_pb2.CheckRequest, context, player, game) -> mafia_pb2.CheckResponse:
        game.check(player.id, request.player_id)

        logging.info(f"{game.id}: {player.name}({player.id}) ? {request.player_id}")
        return mafia_pb2.CheckResponse(mafias=[self.player_id_to_player[player_id] for player_id in game.checked_ids])

    @check(mafia_pb2.PublishResponse())
    async def Publish(self, request: mafia_pb2.PublishRequest, context, player, game) -> mafia_pb2.PublishResponse:
        game.publish(player.id, request.decision)

        logging.info(f"{game.id}: {player.name}({player.id}) P {request.decision}")
        return mafia_pb2.PublishResponse()

    async def GameProcess(self, request: mafia_pb2.GameProcessRequest, context) -> typing.Iterable[mafia_pb2.GameProcessResponse]:
        if request.token not in self.token_to_player:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details(f"Player {request.token} not registered")
            yield mafia_pb2.GameProcessResponse()
            return

        player = self.token_to_player[request.token]

        if player.id not in self.player_id_to_game_id:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Player {player.name}({player.id}) isn't playing any game")
            yield mafia_pb2.GameProcessResponse()
            return

        game_id = self.player_id_to_game_id[player.id]

        if game_id not in self.game_id_to_game:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Game {game_id} is broken")
            yield mafia_pb2.GameProcessResponse()
            return

        game = self.game_id_to_game[game_id]

        logging.info(f'{game.id}: {player.name}({player.id}) process')

        game.start()
        await game.event_started.wait()

        while True:
            game.start_night()

            player_info = game.player_id_to_player_info[player.id]

            yield mafia_pb2.GameProcessResponse(
                night=mafia_pb2.GameProcessResponse.StartNight(
                    is_alive=player_info.is_alive,
                    role=player_info.role,
                    players=[self.player_id_to_player[player_id] for player_id in
                             game.get_alive_players_ids() - {player.id}],
                    mafias=[self.player_id_to_player[player_id] for player_id in
                            game.get_alive_mafias_ids() - {
                                player.id}] if player_info.is_mafia() or not player_info.is_alive else []
                )
            )

            logging.info(f'{game.id}: {player.name}({player.id}) night started...')
            await game.event_killed.wait()
            await game.event_checked.wait()
            logging.info(f'{game.id}: {player.name}({player.id}) night ended...')
            await asyncio.sleep(5)

            winner = game.get_winner()
            if winner is not None:
                yield mafia_pb2.GameProcessResponse(
                    end=mafia_pb2.GameProcessResponse.EndGame(
                        winner=winner
                    )
                )

            game.start_day()

            detective_id = game.get_alive_detective_id()
            yield mafia_pb2.GameProcessResponse(
                day=mafia_pb2.GameProcessResponse.StartDay(
                    is_alive=game.player_id_to_player_info[player.id].is_alive,
                    players=[self.player_id_to_player[player_id] for player_id in
                             game.get_alive_players_ids() - {player.id}],
                    mafias=[self.player_id_to_player[player_id] for player_id in
                            game.get_alive_mafias_ids()] if game.checked_decision and detective_id else [],
                    detective=self.player_id_to_player[detective_id] if detective_id else None
                )
            )

            logging.info(f'{game.id}: {player.name}({player.id}) day started...')
            await game.event_killed.wait()
            logging.info(f'{game.id}: {player.name}({player.id}) day ended...')
            await asyncio.sleep(5)

            winner = game.get_winner()
            if winner is not None:
                yield mafia_pb2.GameProcessResponse(
                    end=mafia_pb2.GameProcessResponse.EndGame(
                        winner=winner
                    )
                )


async def serve(host, port):
    server = grpc.aio.server()
    mafia_pb2_grpc.add_MafiaServicer_to_server(EService(), server)
    server.add_insecure_port(f'{host}:{port}')
    await server.start()
    await server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="[%(asctime)s] [%(levelname)s] [%(name)s] [%(funcName)s():%(lineno)s] %(message)s")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = os.environ.get("PORT", 9000)
    asyncio.run(serve(HOST, PORT))

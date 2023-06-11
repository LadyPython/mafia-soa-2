import logging
import os
import time

import grpc

from art import *
from simple_term_menu import TerminalMenu
import colorful as cf

import random
import mafia_pb2
import mafia_pb2_grpc

cf.use_style("solarized")
MIN_PLAYERS = 4


def print_grpc_error(e: grpc.RpcError):
    print(f"{cf.red}gRPC error {e.code()}:{cf.reset} {e.details()}")


def style_role(role: mafia_pb2.Role):
    match role:
        case mafia_pb2.ROLE_MAFIA:
            style = cf.bold_red
        case mafia_pb2.ROLE_DETECTIVE:
            style = cf.bold_green
        case mafia_pb2.ROLE_VILLAGER:
            style = cf.bold
    return f"{style}{mafia_pb2.Role.Name(role)[5:]}{cf.reset}"


class Client:
    def __init__(self):
        self.name = None
        self.stub = None
        self.token = None
        self.is_auto = False

    def start(self):
        tprint("Mafia online")
        print("Greetings! ✌(◕‿-)✌")
        self.set_name()
        print()
        self.connect_to_server()
        print()
        self.create_or_join_game()
        print()
        self.wait_players()
        print()
        self.get_role()
        print()
        self.play_game()

    def choose_player(self, players: list[mafia_pb2.Player]) -> mafia_pb2.Player:
        if self.is_auto:
            return random.choice(players)

        options = [f"{player.name}({player.id})" for player in players]
        menu = TerminalMenu(options)
        return players[menu.show()]

    def set_name(self):
        self.name = input("State your name: ")
        while not self.name:
            print("\033[F\033[K", end="")
            self.name = input(f"{cf.red}Name cannot be empty!{cf.reset} State your name: ")

    def connect_to_server(self):
        while self.stub is None:
            try:
                address = input(
                    f"{self.name}, provide the server address for connection (HOST:PORT) (leave empty for default): ")
                if not address:
                    address = f"{HOST}:{PORT}"
                    print(f"{cf.yellow}Address is empty.{cf.reset} Connecting to default {address}...")
                channel = grpc.insecure_channel(address)
                stub = mafia_pb2_grpc.MafiaStub(channel)
                response = stub.Connect(mafia_pb2.ConnectRequest(name=self.name))
                self.token = response.token
                self.stub = stub
            except grpc.RpcError as e:
                print_grpc_error(e)
        print(f"Successfully connected to {address}!")

    def create_game(self):
        while True:
            required_players_cnt = input("How many players would you like to have? ")
            if not required_players_cnt.isnumeric():
                print(f"Specify the {cf.red}number{cf.reset}.")
            elif int(required_players_cnt) < MIN_PLAYERS:
                print(f"At least {cf.red}{MIN_PLAYERS} players is required{cf.reset}!")
            else:
                required_players_cnt = int(required_players_cnt)
                break

        print()
        while True:
            try:
                response = self.stub.CreateGame(
                    mafia_pb2.CreateGameRequest(token=self.token, required_players_cnt=required_players_cnt))
                break
            except grpc.RpcError as e:
                print_grpc_error(e)
        print(f"A game with {required_players_cnt} players has been successfully created. "
              f"Use the code {cf.bold_blue}{response.code}{cf.reset} to join.")

    def join_game(self):
        while True:
            try:
                code = input("Enter the game code: ")
                self.stub.JoinGame(mafia_pb2.JoinGameRequest(token=self.token, code=code))
                break
            except grpc.RpcError as e:
                print_grpc_error(e)
        print(f"You have successfully joined the game {code}!")

    def create_or_join_game(self):
        menu = TerminalMenu(["Create game", "Join game"])
        result = menu.show()
        if result == 0:
            self.create_game()
        elif result == 1:
            self.join_game()

    def wait_players(self):
        print(f"Wait for others to join...")
        print()
        while True:
            try:
                response = self.stub.ListPlayers(mafia_pb2.ListPlayersRequest(token=self.token))
                players = response.players
                print("\033[F\033[K", end="")
                print(f"Players({len(players)}/{response.required_players_cnt}):",
                      *(f"{cf.blue}{player.name}{cf.reset}({player.id})" for player in players))
                if len(players) == response.required_players_cnt:
                    break
            except grpc.RpcError as e:
                print_grpc_error(e)
            time.sleep(5)

    def get_role(self):
        response = self.stub.GetRole(mafia_pb2.GetRoleRequest(token=self.token))
        print(f"You are {style_role(response.role)}!")

    def vote(self, players: list[mafia_pb2.Player]):
        print("It's time to vote for someone to eliminate!")
        player = self.choose_player(players)
        self.stub.VoteDay(mafia_pb2.VoteDayRequest(token=self.token, player_id=player.id))
        print(f"You successfully voted for {player.name}({player.id})")

    def day(self, is_alive: bool, players: list[mafia_pb2.Player], mafias: list[mafia_pb2.Player],
            detective: mafia_pb2.Player | None):
        print("The new ☀ day ☀ started.")
        print(f"Other alive players:", *[f"{cf.blue}{player.name}{cf.reset}({player.id})" for player in players])

        if mafias:
            print(f"{cf.green}{detective.name}{cf.reset}({detective.id}) decided to publish mafias:",
                  *[f"{cf.red}{player.name}{cf.reset}({player.id})" for player in mafias])

        if not is_alive:
            print(f"You are {cf.bold}SPIRIT{cf.reset}!")
            return

        self.vote(players)

    def publish(self, mafias: list[mafia_pb2.Player]):
        if not mafias:
            print(f"You did not find any mafias :(")
            self.stub.Publish(mafia_pb2.PublishRequest(token=self.token, decision=False))
            return

        print(f"You know about mafias:", *[f"{cf.red}{player.name}{cf.reset}({player.id})" for player in mafias])
        print(f"Do you want to publish it?")
        options = ["yes", "no"]
        if self.is_auto:
            result = random.choice(options)
        else:
            menu = TerminalMenu(options)
            result = options[menu.show()]

        self.stub.Publish(mafia_pb2.PublishRequest(token=self.token, decision=result == "yes"))

    def check(self, players: list[mafia_pb2.Player]):
        print("It's time to check someone!")

        player = self.choose_player(players)
        response = self.stub.Check(mafia_pb2.CheckRequest(token=self.token, player_id=player.id))
        print(f"You successfully checked {player.name}({player.id})")
        self.publish(response.mafias)

    def kill(self, players: list[mafia_pb2.Player], mafias: list[mafia_pb2.Player]):
        print("It's time to vote for someone to kill!")

        if mafias:
            print("Other mafias:", *[f"{player.name}({player.id})" for player in mafias])
        else:
            print("You are the only mafia present.")

        player = self.choose_player(players)
        self.stub.VoteNight(mafia_pb2.VoteNightRequest(token=self.token, player_id=player.id))
        print(f"You have successfully voted for {player.name}({player.id}).")

    def night(self, is_alive: bool, role: mafia_pb2.Role, players: list[mafia_pb2.Player],
              mafias: list[mafia_pb2.Player]):
        print("The ✦ night ✦ has begun.")
        if not is_alive:
            print(f"You are {cf.bold}SPIRIT{cf.reset}!")
            return

        match role:
            case mafia_pb2.ROLE_DETECTIVE:
                self.check(players)
            case mafia_pb2.ROLE_MAFIA:
                self.kill(players, mafias)
            case mafia_pb2.ROLE_VILLAGER:
                print("Waiting for the mafias and detective to take their actions...")

    def play_game(self):
        menu = TerminalMenu(["Manual play", "Auto bot"])
        ans = menu.show()
        self.is_auto = ans == 1

        for response in self.stub.GameProcess(mafia_pb2.GameProcessRequest(token=self.token)):
            match response.WhichOneof("event"):
                case "day":
                    self.day(response.day.is_alive, response.day.players, response.day.mafias, response.day.detective)
                case "night":
                    self.night(response.night.is_alive, response.night.role, response.night.players,
                               response.night.mafias)
                case "end":
                    print(f"{style_role(response.end.winner)}s are winners!")
                    break
            print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="[%(asctime)s] [%(levelname)s] [%(name)s] [%(funcName)s():%(lineno)s] %(message)s")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = os.environ.get("PORT", 9000)
    client = Client()
    client.start()

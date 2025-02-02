from __future__ import annotations

import asyncio
import websockets

import json
from queue import Queue, Empty, Full

from world import UP, DOWN, LEFT, RIGHT
from agent import AbstractSnakeAgent

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Sequence
    from type_hints import Direction
    from world import SnakeWorld


class ClientSnakeAgentProxy(AbstractSnakeAgent):
    """Implements a snake agent which is controlled by requests coming from another
    thread. It makes the proxy between a SnakeWorld and a Server.
    """
    def __init__(self, world: SnakeWorld, initial_pos: Sequence[Direction], initial_dir: Direction) -> None:
        assert initial_dir in (UP, DOWN, LEFT, RIGHT)
        super().__init__(world, initial_pos)
        self.initial_dir = initial_dir
        self.dir = initial_dir
        self.dir_requests: Queue[Direction] = Queue(maxsize=5)

    # ---- SnakeWorld side
    def reset(self) -> None:
        super().reset()
        self.dir = self.initial_dir
        while not self.dir_requests.empty():
            try:
                self.dir_requests.get_nowait()
            except Empty:
                pass

    def decide_direction(self) -> None:
        try:
            self.dir = self.dir_requests.get_nowait()
        except Empty:
            pass

    def get_direction(self) -> Direction:
        return self.dir

    # ---- Server side
    def add_dir_request(self, request: Direction) -> None:
        try:
            self.dir_requests.put_nowait(request)
        except Full:
            pass


class ClientHandler:
    def __init__(self, websock, agent: ClientSnakeAgentProxy):
        self.websock = websock
        self.agent = agent

    async def kick_client(self):
        self.agent.die()
        await self.websock.close()
        print(f"[{self.websock.remote_address}] kicked")

    async def handle_client(self):
        async for message in self.websock:
            print(f"[{self.websock.remote_address}] message: {message}")
            match json.dumps(message):
                case [int(dx), int(dy)]:
                    if (direction := (dx, dy)) in (UP, DOWN, LEFT, RIGHT):
                        self.agent.add_dir_request(direction)
                    else:
                        await self.kick_client()
                case _:
                    await self.kick_client()


class ServerSnakeWorld(SnakeWorld):
    ...


class Server:
    def __init__(self, world: SnakeWorld):
        self.world = world
        self.clients = set()

    async def on_connect(self, client):
        print(f"Connected: {client.remote_address}")
        self.clients.add(client)
        await ClientHandler(client).handle_client()
        self.clients.remove(client)



if __name__ == "__main__":
    host = "127.0.0.1"
    port = 50000

    server = Server()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(websockets.serve(server.on_connect, host, port))
    loop.run_forever()

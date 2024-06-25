import asyncio
import websockets
import json
from random import randint
from colorama import Fore, Style, Back
from time import sleep, time

class Battle:
    """Represents a battle session in the Pixelverse game."""
    win_count = 0
    lose_count = 0
    total_coin = 0
    kabur_count = 0

    def __init__(self):
        """Initializes the Battle object with game settings."""
        self.url = 'https://api-clicker.pixelverse.xyz/api/users'
   
        with open('./config.json', 'r') as file:
            config = json.load(file)

        self.secret = config['secret']
        self.tgId = config['tgId']
        self.initData = config['initData']
        self.hitRate = config['hitRate']
        self.player_id = config['player_id']
        self.websocket: websockets.WebSocketClientProtocol = None
        self.battleId = ""
        self.superHit = False
        self.strike = {
            "defense": False,
            "attack": False
        }

        self.space = ""
        self.stop_event = asyncio.Event()

    async def sendHit(self):
        """Continuously sends 'HIT' actions during the battle."""
        while not self.stop_event.is_set():
            if self.superHit:
                await asyncio.sleep(0.3)
                continue

            content = [
                "HIT",
                {
                    "battleId": self.battleId
                }
            ]
            try:
                await self.websocket.send(f"42{json.dumps(content)}")
            except:
                return
            await asyncio.sleep(self.hitRate)

    async def listenerMsg(self):
        if Battle.win_count + Battle.lose_count > 0:
            win_rate = (Battle.win_count / (Battle.win_count + Battle.lose_count)) * 100
        else:
            win_rate = 0  # Atau nilai default lain yang sesuai
    
        """Listens for and processes incoming messages from the game server."""
        while not self.stop_event.is_set():
            try:
                data = await self.websocket.recv()
                # print(data)
            except Exception as err:
                self.stop_event.set()
                return

            if data.startswith('42'):
                data = json.loads(data[2:])  # Remove prefix "42"
                # print(data)
                if data[0] == "HIT":
                    player1_id = data[1]['player1']['userId']
                    player1_energy = data[1]['player1']['energy']
                    player2_id = data[1]['player2']['userId']
                    player2_energy = data[1]['player2']['energy']
                    # print(self.player_id)
                    # Tentukan siapa yang adalah 'r_ghalibie' berdasarkan userId
                    if player1_id == self.player_id: 
                        my_energy = player1_energy
                        enemy_energy = player2_energy
                    elif player2_id == self.player_id:
                        my_energy = player2_energy
                        enemy_energy = player1_energy
                    else:
                        continue  # Jika tidak ada userId yang cocok, lanjutkan ke data berikutnya

                    # Cek kondisi untuk kabur
                    if my_energy < 100 and enemy_energy > 170:
                        print(f"✅ Anti Lose Activated                                                                    \n\n")
                        Battle.kabur_count += 1
                        await self.websocket.close()
                        self.stop_event.set()
                        return

                    print(
                        f"💥 {Fore.GREEN+Style.BRIGHT}{self.player1['name']} ({player1_energy}) {Fore.WHITE + Style.BRIGHT}VERSUS{Style.RESET_ALL} {Fore.BLUE+Style.BRIGHT} ({player2_energy}) {self.player2['name']}{Style.RESET_ALL}"
                         , end="\r" , flush=True)
                    
                    # Check if the battle should end
                    if my_energy <= 0 or enemy_energy <= 0:
                        result = 'WIN' if enemy_energy <= 0 else 'LOSE'
                        reward = randint(10, 100)  # Example reward, adjust as needed
                        if result == 'WIN':
                            Battle.win_count += 1
                            Battle.total_coin += reward
                        else:
                            Battle.lose_count += 1
                        win_rate = (Battle.win_count / (Battle.win_count + Battle.lose_count)) * 100
                        await asyncio.sleep(0.5)
                        print('')
                        print(
                            f"⚔️ You {Fore.GREEN+Style.BRIGHT if result == 'WIN' else Fore.RED+Style.BRIGHT}{result}{Style.RESET_ALL} {Fore.YELLOW+Style.BRIGHT}{reward}{Style.RESET_ALL} coins !")
                        print(f"🏆 {Fore.GREEN+Style.BRIGHT}{Battle.win_count} Win / {Fore.RED+Style.BRIGHT}{Battle.lose_count} Lose {Style.RESET_ALL}| {Fore.CYAN+Style.BRIGHT} Win Rate: {win_rate:.2f}%                                                    ", flush=True)
                        print(f"🟡 Total Coins: {Fore.YELLOW+Style.BRIGHT}{Battle.total_coin}\n{Style.RESET_ALL}\n\n")
                        self.stop_event.set()
                        return
                    
                elif data[0] == "SET_SUPER_HIT_PREPARE":
                    self.superHit = True

                elif data[0] == "SET_SUPER_HIT_ATTACK_ZONE":
                    content = [
                        "SET_SUPER_HIT_ATTACK_ZONE",
                        {
                            "battleId": self.battleId,
                            "zone": randint(1, 4)
                        }
                    ]
                    await self.websocket.send(f"42{json.dumps(content)}")
                    self.strike['attack'] = True

                elif data[0] == "SET_SUPER_HIT_DEFEND_ZONE":
                    content = [
                        "SET_SUPER_HIT_DEFEND_ZONE",
                        {
                            "battleId": self.battleId,
                            "zone": randint(1, 4)
                        }
                    ]
                    await self.websocket.send(f"42{json.dumps(content)}")
                    self.strike['defense'] = True

                elif data[0] == "END":
                    result = data[1]['result']
                    reward = data[1]['reward']
                    if result == 'WIN':
                        Battle.win_count += 1
                        Battle.total_coin += reward  # Menambahkan reward ke total coins
                    elif result == 'LOSE':
                        Battle.lose_count += 1
                    win_rate = (Battle.win_count / (Battle.win_count + Battle.lose_count)) * 100
                    await asyncio.sleep(0.5)
                    print('')
                    print(
                            f"⚔️ You {Fore.GREEN+Style.BRIGHT if result == 'WIN' else Fore.RED+Style.BRIGHT}{result}{Style.RESET_ALL} {Fore.YELLOW+Style.BRIGHT}{reward}{Style.RESET_ALL} coins !")
                    print(f"🏆 {Fore.GREEN+Style.BRIGHT}{Battle.win_count} Win / {Fore.RED+Style.BRIGHT}{Battle.lose_count} Lose {Style.RESET_ALL}| {Fore.CYAN+Style.BRIGHT} Win Rate: {win_rate:.2f}%                                                    ", flush=True)
                    print(f"🟡 Total Coins: {Fore.YELLOW+Style.BRIGHT}{Battle.total_coin}{Style.RESET_ALL}\n\n")
                    self.stop_event.set()
                    return

                try:
                    if (self.strike['attack'] and not self.strike['defense']) or (
                            self.strike['defense'] and not self.strike['attack']):
                        await self.websocket.recv()
                        await self.websocket.recv()

                    if self.strike['attack'] and self.strike['defense']:
                        await self.websocket.recv()
                        await self.websocket.send("3")
                        await self.websocket.recv()
                        self.superHit = False
                except:
                    pass

    async def handleWssFreeze(self, seconds: int):
        timeToReach = time() + seconds

        while not self.stop_event.is_set():
            if time() > timeToReach:
                print(f"⚠️ {Fore.RED+Style.BRIGHT}WSS Closed{Style.RESET_ALL}")
                self.websocket.close()
                print(f"⚠️ {Fore.YELLOW+Style.BRIGHT}Bot is restarting ...{Style.RESET_ALL}")

            await asyncio.sleep(0.001)

    async def connect(self):
        """Establishes a connection to the game server and starts the battle."""
        uri = "wss://api-clicker.pixelverse.xyz/socket.io/?EIO=4&transport=websocket"
        print(f"\n{Fore.YELLOW+Style.BRIGHT}🏟️ Memasuki Arena..{Style.RESET_ALL}")

        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    self.websocket = websocket

                    # print("WebSocket connected, waiting for initial data...")
                    data = await websocket.recv()
                    # print(f"Received initial data: {data}")

                    content = {
                        "tg-id": self.tgId,
                        "secret": self.secret,
                        "initData": self.initData
                    }
                    await websocket.send(f"40{json.dumps(content)}")
                    print(f"{Fore.YELLOW+Style.BRIGHT}🔍 Mencari Lawan..")

                    await websocket.recv()
                    data = await websocket.recv()
                    # print(f"Received data after sending initial content: {data}")

                    data = json.loads(data[2:])  # Remove prefix "42"

                    try:
                        self.battleId = data[1]['battleId']
                        print(f"👹{Fore.GREEN+Style.BRIGHT} Lawan ditemukan")
                    except KeyError:
                        print(f"💀{Fore.RED+Style.BRIGHT} Lawan tidak ditemukan, mencari lagi.", flush=True)
                        await asyncio.sleep(1)  # Tunggu sebentar sebelum mencoba lagi
                        continue  # Retry connection

                    self.player1 = {
                        "name": data[1]['player1']['username']
                    }
                    self.player2 = {
                        "name": data[1]['player2']['username']
                    }

                    for i in range(5, 0, -1):
                        print(
                            f"{Fore.CYAN+Style.BRIGHT}⚔️ Battle dimulai dalam {Back.RED + Fore.WHITE}{i}{Style.RESET_ALL}.                            ",
                             end="\r", flush=True)
                        await asyncio.sleep(1)
                        
                    # print("gelud dimulai...")
                    listenerMsgTask = asyncio.create_task(self.listenerMsg())
                    hitTask = asyncio.create_task(self.sendHit())
                    
                    await asyncio.gather(listenerMsgTask, hitTask)
                    break  # Exit the loop if connection is successful

            except websockets.exceptions.InvalidStatusCode as e:
                print(f"🚨{Fore.RED+Style.BRIGHT} Gagal Memasuki Arena {e.status_code}. Mencoba lagi..", flush=True)
                await asyncio.sleep(5)  # Wait before retrying
            except Exception as e:
                print(f"⚠️ Koneksi Terputus: {e}. Mencoba lagi..", end="\r" , flush=True)
                await asyncio.sleep(5)  # Wait before retrying

async def main():
    while True:
        battle = Battle()
        await battle.connect()

if __name__ == "__main__":
    asyncio.run(main())
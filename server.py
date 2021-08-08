import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import random

thread_pool = ThreadPoolExecutor()


class MilionerzyServerClientProtocol(asyncio.Protocol):
    start_game = False
    poprawna = None
    wykorzystane_pytania = []
    aktualne_pytanie = []
    odp_klienta=None
    liczba_poprawnych_odp=0
    nagrody=['1000', '5000','10000', '20000', '40000', '75000', '125000', '250000', '500000', '1000000']
    dostepne_kola={'z':True, 'p':True}
    f = open("pytania.txt", "r")
    lines = f.readlines()
    def connection_made(self, transport):
        self.transport = transport
        print("Connected")
        self.transport.write("Witaj w grze milionerzy! Potwierdz uczestnictwo wpisujac OK".encode())

    def data_received(self, data: bytes) -> None:
        message = data.decode('utf-8')
        print('Odebrano wiadomosc: {}'.format(message))
        self.odp_klienta=message
        if self.start_game == False:
            if message[:2] == "OK":
                self.start_game = True
                self.transport.write("Swietnie! Oto pierwsze pytanie:".encode())
                task = asyncio.create_task(self.async_milionerzy_losuj_pytanie())
                task = asyncio.create_task(self.async_milionerzy_wyslij_pytanie())
        else:
            if (self.liczba_poprawnych_odp == 2 or self.liczba_poprawnych_odp == 7) and message[:1]=='k':
                self.transport.write("Twoj wynik to {}".format(self.nagrody[self.liczba_poprawnych_odp]).encode())
            elif message[:1] == 'z' and self.dostepne_kola['z']==True:
                self.dostepne_kola['z']=False
                task = asyncio.create_task(self.async_milionerzy_zamiana_pytania())
            elif message[:1] == 'p' and self.dostepne_kola['p']==True:
                self.dostepne_kola['p']=False
                task = asyncio.create_task(self.async_milionerzy_kolo_pol_na_pol())
            else:
                task = asyncio.create_task(self.async_milionerzy_sprawdz_odp(message[:1]))
                if message[:1]==self.poprawna and self.liczba_poprawnych_odp!=1 and self.liczba_poprawnych_odp!=6:
                    task = asyncio.create_task(self.async_milionerzy_losuj_pytanie())
                    task = asyncio.create_task(self.async_milionerzy_wyslij_pytanie())

    async def async_milionerzy_wyslij_pytanie(self):
        self.transport.write("Aktualnie grasz o {}".format(self.nagrody[self.liczba_poprawnych_odp]).encode())
        for i in self.aktualne_pytanie:
            self.transport.write(i.encode())
    async def async_milionerzy_sprawdz_odp(self, odp):
        if odp == self.poprawna:
            self.liczba_poprawnych_odp+=1
            self.transport.write("Poprawna odpowiedz!".encode())
            if self.liczba_poprawnych_odp == 2 or self.liczba_poprawnych_odp == 7:
                self.transport.write("Brawo! Osiagnales kwote gwarantowana! Czy chcesz grac dalej(g)? Czy konczysz gre(k)?".encode())
        else:
            self.transport.write('poprawna odpowiedz to {}'.format(self.poprawna).encode())

    # Losowanie pytania. Zapisywanie uzytych pytan do tablicy
    async def async_milionerzy_losuj_pytanie(self):
        self.aktualne_pytanie.clear()

        # Mamy 21 pytania
        wylosowane_pytanie = random.randrange(0, 30, 6)

        if len(self.wykorzystane_pytania) == 18:  # 18 = obecna ilosc pytan
            print("wszystkie pytania zostaly zadane!")

        elif wylosowane_pytanie in self.wykorzystane_pytania:
            while wylosowane_pytanie in self.wykorzystane_pytania:
                wylosowane_pytanie = random.randrange(0, 100, 6)

        self.wykorzystane_pytania.append(wylosowane_pytanie)
        for i in range(wylosowane_pytanie, wylosowane_pytanie + 5):
            print(self.lines[i])
            self.aktualne_pytanie.append(self.lines[i])

        self.poprawna = self.lines[wylosowane_pytanie + 5]
        self.poprawna = str(self.poprawna[0])  # poprawna odpowiedz np. A, B, C, D

    async def async_milionerzy_kolo_pol_na_pol(self):
        array_of_numbers = []
        if self.poprawna == 'A':
            array_of_numbers = [1, 2, 3]
        elif self.poprawna == 'B':
            array_of_numbers = [0, 2, 3]
        elif self.poprawna == 'C':
            array_of_numbers = [0, 1, 3]
        elif self.poprawna == 'D':
            array_of_numbers = [0, 1, 2]

        two_answers = random.sample(array_of_numbers, 2)
        self.aktualne_pytanie.pop(int(two_answers[0]))
        self.aktualne_pytanie.pop(int(two_answers[1]))


# odp = input("Podaj odp: ")


loop = asyncio.get_event_loop()
coroutine = loop.create_server(MilionerzyServerClientProtocol, 'localhost', 1000)

server = loop.run_until_complete(coroutine)

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()

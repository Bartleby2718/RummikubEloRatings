from typing import List
import datetime

K_FACTOR: int = 32  # https://en.wikipedia.org/wiki/Elo_rating_system#Mathematical_details
INPUT_FILE_NAME: str = 'rummikub.csv'
OUTPUT_FILE_NAME: str = 'elo_ratings.csv'


class Player:
    def __init__(self, name: str = ''):
        self.name: str = name
        self.rating: float = 1000  # initial ELO rating


class GameRecord:
    def __init__(self, date: str, losers: List[Player], winner: Player):
        date_str: List[str] = date.split('/')
        self.date = datetime.date(int(date_str[2]), int(date_str[0]), int(date_str[1]))
        self.losers: List[Player] = losers
        self.winner: Player = winner


def process_game_records(players: List[Player], records: List[GameRecord]) -> List[Player]:
    for record in records:
        winner = record.winner
        # Formula taken from https://en.wikipedia.org/wiki/Elo_rating_system#Theory
        # Because we ended the game once the first place was determined,
        # I thought of the winner having played against each non-winner ("loser" in this script)
        # Credit: http://www.tckerrigan.com/Misc/Multiplayer_Elo/
        for loser in record.losers:
            winner_expected_chance = 1 / (1 + pow(10, ((loser.rating - winner.rating) / 400)))
            loser_expected_chance = 1 - winner_expected_chance
            winner.rating += K_FACTOR * (1 - winner_expected_chance)  # 1 for winner
            loser.rating += K_FACTOR * (0 - loser_expected_chance)  # 0 for loser
    return players


def main():
    # initialize a list of players
    players: List[Player] = []
    records: List[GameRecord] = []

    # import csv file
    with open(INPUT_FILE_NAME, encoding='utf8') as file:
        # process the first line (player names are in the header)
        line: str = file.readline().strip()
        columns: List[str] = line.split(',')
        for cell in columns[1:]:
            player = Player(cell)
            players.append(player)

        # process the remaining lines (game records)
        for line in file:
            columns: List[str] = line.strip().split(',')
            date: str = columns[0]
            losers: List[Player] = []
            winner = Player()
            for index, value in enumerate(columns[1:]):
                if value == '0':
                    player = players[index]
                    losers.append(player)
                elif value == '1':  # Each line must be guaranteed to have 1 once and only once
                    winner = players[index]
            record = GameRecord(date, losers, winner)
            records.append(record)

    players = process_game_records(players, records)

    # output result
    with open(OUTPUT_FILE_NAME, 'w', encoding='utf8') as file:
        players.sort(key=lambda x: float(x.rating), reverse=True)
        for player in players:
            file.write('{},{:.2f}\n'.format(player.name, player.rating))


if __name__ == '__main__':
    main()

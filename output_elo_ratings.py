from typing import List
import datetime
import matplotlib.pyplot as plt
import numpy as np

K_FACTOR: int = 32  # https://en.wikipedia.org/wiki/Elo_rating_system#Mathematical_details
INPUT_FILE_NAME: str = 'rummikub.csv'
OUTPUT_FILE_NAME: str = 'elo_ratings.csv'
INITIAL_ELO_RATING: float = 1000


class Player:
    def __init__(self, name: str = ''):
        self.name: str = name
        self.rating: float = INITIAL_ELO_RATING


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
        file.write('Player,Elo Rating\n')
        players.sort(key=lambda x: float(x.rating), reverse=True)
        for player in players:
            file.write('{},{:.2f}\n'.format(player.name, player.rating))


def visualize_rankings(rankings_file_name: str, save_image_file=True):
    # Fixing random state for reproducibility
    np.random.seed(19680801)

    plt.rcdefaults()
    fig, ax = plt.subplots()

    players: List[str] = []
    ratings: List[float] = []
    with open(rankings_file_name) as file:
        file.readline()  # skip the header
        for line in file:
            columns = line.split(',')
            player: str = columns[0]
            rating: float = float(columns[1])
            players.append(player)
            ratings.append(rating)
    members = np.arange(len(players))

    ax.barh(members, ratings, align='center')
    ax.set_yticks(members)
    ax.set_yticklabels(players)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_title('Bapul Team Rummikub Rankings ')
    ax.set_xlabel('Elo Ratings')
    plt.axvline(x=INITIAL_ELO_RATING, color='gray', linewidth=.5)

    if save_image_file:
        plt.savefig('Rankings.png')
    plt.show()


if __name__ == '__main__':
    main()
    visualize_rankings(OUTPUT_FILE_NAME)

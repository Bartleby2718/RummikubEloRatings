from collections import OrderedDict
from typing import Dict, List
import datetime
import imageio
import matplotlib.pyplot as plt
import numpy as np
import os

K_FACTOR: int = 32  # https://en.wikipedia.org/wiki/Elo_rating_system#Mathematical_details
CSV_FILES_DIRECTORY: str = 'csv_files'
IMAGE_FILES_DIRECTORY: str = 'image_files'
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


def process_game_records(players: List[Player], records: List[GameRecord]) -> Dict[datetime.date, dict]:
    initial_date: datetime.date = None
    daily_rankings: Dict[datetime.date, dict] = {}
    last_date_updated: datetime.date = None
    for record in records:
        # Add initial rankings
        if initial_date is None:
            initial_date = record.date - datetime.timedelta(days=1)
            initial_ratings: Dict[str, float] = {player.name: player.rating for player in players}
            daily_rankings.update({initial_date: initial_ratings})
        if last_date_updated is None:
            last_date_updated = initial_date

        # Save rankings if a record with new date appears
        if record.date not in daily_rankings:
            rankings: Dict[str, float] = {player.name: player.rating for player in players}
            daily_rankings.update({last_date_updated: rankings})

        # in any case, update the ratings
        winner: Player = record.winner
        # Formula taken from https://en.wikipedia.org/wiki/Elo_rating_system#Theory
        # Because we ended the game once the first place was determined,
        # I thought of the winner having played against each non-winner ("loser" in this script)
        # Credit: http://www.tckerrigan.com/Misc/Multiplayer_Elo/
        for loser in record.losers:  # loser: Player
            winner_expected_chance: float = 1 / (1 + pow(10, ((loser.rating - winner.rating) / 400)))
            loser_expected_chance: float = 1 - winner_expected_chance
            winner.rating += K_FACTOR * (1 - winner_expected_chance)  # 1 for winner
            loser.rating += K_FACTOR * (0 - loser_expected_chance)  # 0 for loser

        # Update the date as well
        last_date_updated = record.date

    # Save the final rankings
    rankings: Dict[str, float] = {player.name: player.rating for player in players}
    daily_rankings.update({last_date_updated: rankings})
    return daily_rankings


def main():
    # initialize a list of players
    players: List[Player] = []
    records: List[GameRecord] = []

    # import csv file
    with open(INPUT_FILE_NAME, encoding='utf8') as file:
        # process the first line (player names are in the header)
        line: str = file.readline().strip()
        columns: List[str] = line.split(',')
        for cell in columns[1:]:  # cell: str
            player = Player(cell)
            players.append(player)

        # process the remaining lines (game records)
        for line in file:  # line: str
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

    daily_rankings = process_game_records(players, records)

    # output result
    with open(OUTPUT_FILE_NAME, 'w', encoding='utf8') as file:
        file.write('Player,Elo Rating\n')
        players.sort(key=lambda x: float(x.rating), reverse=True)
        for player in players:
            file.write('{},{:.2f}\n'.format(player.name, player.rating))

    images: List[imageio.core.util.Array] = []
    image_file_names: List[str] = []

    colors: Dict[str, tuple] = {player.name: tuple(np.random.rand(3, )) for player in players}
    dates: List[datetime.date] = []
    for date, rankings in daily_rankings.items():
        date: datetime.date
        dates.append(date)
        file_name: str = date.strftime('csv_files/DailyRankings%Y%m%d.csv')
        with open(file_name, 'w', encoding='utf8') as file:
            file.write('Player,Elo Rating\n')
            ordered_rankings = OrderedDict(sorted(rankings.items(), key=lambda x: (-x[1], x[0])))
            for player, rating in ordered_rankings.items():
                file.write('{},{:.2f}\n'.format(player, rating))
        image_file_name: str = date.strftime('image_files/DailyRankings%Y%m%d.png')
        image_file_names.append(image_file_name)
        visualize_rankings(file_name, colors, date.strftime('%Y-%m-%d'), True, image_file_name)
        image: imageio.core.util.Array = imageio.imread(image_file_name)
        images.append(image)
    imageio.mimsave('rankings.gif', images, duration=0.5)


def visualize_rankings(rankings_file_name: str, colors=None,
                       title: str = 'Bapul Team Rummikub Rankings', save_image_file: bool = False,
                       image_file_name='Rankings.png'):
    # Fixing random state for reproducibility
    np.random.seed(19680801)

    plt.rcdefaults()
    fig, ax = plt.subplots(figsize=(6.4, 4.8))  # ax: plt.Axes
    ax.set_xlim(right=1250)

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
    ordered_colors = None if colors is None else [colors[player] for player in players]
    ax.barh(members, ratings, align='center', color=ordered_colors)

    ax.set_xticks([200 * i for i in range(7)])
    ax.set_yticks(members)
    ax.set_yticklabels(players)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_title(title)
    ax.set_xlabel('Elo Ratings')
    plt.axvline(x=INITIAL_ELO_RATING, color='gray', linewidth=.5)

    if save_image_file:
        plt.savefig(image_file_name)
    plt.close()


if __name__ == '__main__':
    directories_needed: List[str] = [CSV_FILES_DIRECTORY, IMAGE_FILES_DIRECTORY]
    for directory_name in directories_needed:
        if not os.path.exists(directory_name):
            os.mkdir(directory_name)
    main()
    visualize_rankings(OUTPUT_FILE_NAME, save_image_file=True)

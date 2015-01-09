#! /usr/bin/env python3

import unittest
import yaml
from datetime import datetime, timezone


class Rank(object):

    def __init__(self, value):
        if int(value) == 0:
            raise ValueError('Rank values must be a nonzero integer')
        self.value = int(value)

    def __add__(self, other):
        # adding ranks is nonsensical
        return NotImplemented

    def __sub__(self, other):
        # note that this returns an nonnegative integer, NOT a rank (intentionally)

        # check whether both values have the same sign
        if abs(self.value + other.value) == abs(self.value) + abs(other.value):
            return abs(self.value - other.value)
        else:
            return abs(self.value) + abs(other.value) - 1

    # there's gotta be a better way to do this
    def __iadd__(self, other):
        if other < 0:
            self -= abs(other)
        elif self.value < 0:
            if abs(self.value) > other:
                self.value += other
            else:
                self.value += other + 1
        else:
            self.value += other
        return self

    def __isub__(self, other):
        if other < 0:
            self += abs(other)
        elif self.value < 0:
            self.value -= other
        else:
            if self.value > other:
                self.value -= other
            else:
                self.value -= other + 1
        return self

    def __int__(self):
        return self.value

    def __str__(self):
        rank_str = ''
        if self.value < 0:
            rank_str = '{:d}K'.format(-self.value)
        else:
            rank_str = '{:d}D'.format(self.value)
        return rank_str

    def __eq__(self, other):
        return type(other) is type(self) and self.value == other.value

    def __ne__(self, other):
        return type(other) is not type(self) or self.value != other.value

    def __hash__(self):
        return self.value


class Player(object):

    def __init__(self, name, rank, aga_id):
        self.name = name
        self.rank = Rank(rank)
        self.aga_id = aga_id

    def __repr__(self):
        return '<{:s}(name={:s}, rank={:s}, aga_id={:d})>'.format(self.__class__.__name__,
                                                                  self.name, str(self.rank),
                                                                  self.aga_id)

    def __str__(self):
        return '{:s} ({:d}) {:s}'.format(self.name, self.aga_id, str(self.rank))


class Result(object):

    def __init__(self, white, black, winner, time=None):
        if not winner in {white, black}:
            raise ValueError('Winner must be either white or black ladder_id')
        self.white = white
        self.black = black
        self.winner = winner
        if time is None:
            time = datetime.now(timezone.utc)
        self.time = time


class Ladder(object):

    def __init__(self, players=None, standings=None, results=None, base_id=0):
        if standings is None:
            self.standings = []
        else:
            self.standings = standings
        if players is None:
            self.players = {}
        else:
            self.players = players
        if results is None:
            self.results = []
        else:
            self.results = results
        self.id_ctr = base_id

    def __str__(self):
        the_string = 'Ladder standings:'
        position = 1
        for player in self.standings:
            the_string += '\n    {:d}. {:s}'.format(position, str(player))
            position += 1
        return the_string

    def add_players(self, players):
        for player in players:
            self.players[self.id_ctr] = player
            self.id_ctr += 1

    def validate_match(self, white, black):
        player_set = self.players.keys()
        black_pos = self.standings.index(black)
        white_pos = self.standings.index(white)
        if not black in player_set:
            raise ValueError('Black player unknown: {:d}'.format(black))
        if not white in player_set:
            raise ValueError('White player unknown: {:d}'.format(white))
        if black_pos < white_pos:
            raise ValueError('White standing ({:d}) <= black standing ({:d})'
                             .format(white_pos, black_pos))
        pos_diff = black_pos - white_pos
        rank_diff = self.players[white].rank - self.players[black].rank
        if pos_diff > 2 and rank_diff > 2:
            raise ValueError('Rank difference: {:d}, position difference: {:d}'.format(rank_diff,
                                                                                       pos_diff))

    def submit_result(self, result):
        self.validate_match(result.white, result.black)
        if result.winner == result.black:
            self.standings.remove(result.black)
            self.standings.insert(self.standings.index(result.white), result.black)
        self.results.append(result)

    def write_to_yaml(self, stream):
        yaml.dump(self, stream)


class RankTestCase(unittest.TestCase):

    def test_init(self):
        self.assertRaises(ValueError, Rank, 0)

    def test_add(self):
        with self.assertRaises(TypeError):
            value = Rank(1) + Rank(2)
        with self.assertRaises(TypeError):
            value = Rank(1) + 2

    def test_sub(self):
        self.assertEqual(Rank(5) - Rank(1), 4)
        self.assertEqual(Rank(5) - Rank(5), 0)
        self.assertEqual(Rank(5) - Rank(6), 1)
        self.assertEqual(Rank(5) - Rank(-3), 7)
        self.assertEqual(Rank(1) - Rank(-1), 1)

    def test_inc(self):
        rank = Rank(1)
        rank += 1
        self.assertEqual(rank.value, Rank(2).value)
        rank += 5
        self.assertEqual(rank.value, Rank(7).value)
        rank += 0
        self.assertEqual(rank.value, Rank(7).value)
        rank += -1
        self.assertEqual(rank.value, Rank(6).value)
        rank += -6
        self.assertEqual(rank.value, Rank(-1).value)
        rank += -10
        self.assertEqual(rank.value, Rank(-11).value)
        rank += 15
        self.assertEqual(rank.value, Rank(5).value)

    def test_dec(self):
        rank = Rank(-1)
        rank -= 1
        self.assertEqual(rank.value, Rank(-2).value)
        rank -= 5
        self.assertEqual(rank.value, Rank(-7).value)
        rank -= 0
        self.assertEqual(rank.value, Rank(-7).value)
        rank -= -1
        self.assertEqual(rank.value, Rank(-6).value)
        rank -= -6
        self.assertEqual(rank.value, Rank(1).value)
        rank -= -10
        self.assertEqual(rank.value, Rank(11).value)
        rank -= 15
        self.assertEqual(rank.value, Rank(-5).value)

    def test_str(self):
        self.assertEqual(str(Rank(5)), '5D')
        self.assertEqual(str(Rank(1)), '1D')
        self.assertEqual(str(Rank(-5)), '5K')
        self.assertEqual(str(Rank(-1)), '1K')


class LadderTestCase(unittest.TestCase):

    def setUp(self):
        self.players = {0: Player('Andrew', -1, 12345),
                        1: Player('Walther', 5, 12390),
                        2: Player('Milan', -6, 234),
                        3: Player('James', -10, 2399),
                        4: Player('Quinten', 3, 2),
                        }
        self.ladder = Ladder(players=self.players, standings=[0, 1, 2, 3, 4], base_id=5)

    def test_match_valid(self):
        try:
            self.ladder.validate_match(0, 1)
            self.ladder.validate_match(0, 2)
            self.ladder.validate_match(1, 3)
            self.ladder.validate_match(1, 4)
        except ValueError as e:
            self.fail(str(e))

        with self.assertRaises(ValueError):
            self.ladder.validate_match(0, 5)
        with self.assertRaises(ValueError):
            self.ladder.validate_match(1, 5)
        with self.assertRaises(ValueError):
            self.ladder.validate_match(0, 3)
        with self.assertRaises(ValueError):
            self.ladder.validate_match(1, 0)

    def test_submit_result(self):
        result_one = Result(0, 1, 1)
        self.ladder.submit_result(result_one)
        new_standings = [1, 0, 2, 3, 4]
        self.assertEqual(self.ladder.standings, new_standings)

    def test_yaml(self):
        with open('unittest.yaml', 'w+') as stream:
            self.ladder.write_to_yaml(stream)

if __name__ == '__main__':
    unittest.main()

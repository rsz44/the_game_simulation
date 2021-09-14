import random
import copy
from rich.console import Console
import config
import uuid

console = Console()

if config.DEBUG == False:
	console.log = lambda x: x

state = {}

def shuffle(cards_range=[1, 100]):
	cards = list(range(cards_range[0]+1, cards_range[1]))
	random.shuffle(cards)
	return cards

ASC = ['ASC', 1]
DESC = ['DESC', -1]


class EmptyHandException(Exception):
	pass

class LockedCardStack(Exception):

	def __init__(self, player, stack):
		super(CantPlayException, self).__init__(f"Player {player.pid} can't play on this stack, because the stack is locked by {stack.lock}.")

class CantPlayException(Exception):

	def __init__(self, player):
		super(CantPlayException, self).__init__(f"Player {player.pid} can't play with hand {player.hand}")
		

class CardStack(object):
	"""CardStack"""

	def __init__(self, cards_range=[1, 99], step=ASC):
		self.uid = str(uuid.uuid4())[:8]
		self.cards_range = cards_range
		self.cards = []
		self.step = step
		self.lock = None
		self.turn = {}
		self.lock_has_been_forced = False

	def __repr__(self):
		return f'Stack[{self.step[0]}] {self.last}'

	def acquire(self, player):
		if self.lock == None:
			self.lock = player.pid

		if self.lock != player.pid:
			raise ValueError(f"Player {player.pid} acquire lock, but CardStack is acquired by {self.lock}")
		console.log(f'{self} has been locked by {player.pid}')

	def force_release(self):
		self.lock = None
		self.lock_has_been_forced = True

	def release(self, player):
		if self.lock != None and self.lock != player.pid:
			raise ValueError(f"Player {player.pid} release lock, but CardStack is acquired by {self.lock}")
		self.lock = None
		return True

	def locked(self, player):
		if self.lock == None:
			return False
		if self.lock != player.pid:
			return True
		return False

	@property
	def last(self):
		if len(self.cards):
			return self.cards[-1]
		return self.cards_range[0 if self.step[0] == ASC[0] else -1]

	def can_play_card(self, card_number):
		if self.step[0] == ASC[0]:
			if card_number < self.last:
				if card_number == self.last - 10:
					return True
				return False
		else:
			if card_number > self.last:
				if card_number == self.last + 10:
					return True
				return False
		return True

	def put(self, player, card_number, force=False):
		player.hand = [c for c in player.hand if c != card_number]

		if self.locked(player):
			if force:
				self.force_release()
				self.lock_has_been_forced = True
			else:
				raise LockedCardStack(player, self)

		if not self.can_play_card(card_number):
			raise RuntimeError(f"Player {player.pid} can't put the card {card_number} on a {self.step[0]} stack, last card is {self.last}.")

		console.log(f'Player {player.pid} put {card_number} on stack[{self.step[0]}] last card was {self.last}')
		self.cards.append(card_number)

		if not player.pid in self.turn.keys():
			self.turn[player.pid] = []

		self.turn[player.pid].append(card_number)

	def export(self):
		return {
			'cards': self.cards,
			'step': self.step,
			'last': self.last
		}

class TheGamePlayer(object):
	"""TheGamePlayer"""
	def __init__(self, pid, hand_size):
		self.pid = pid
		self.hand_size = hand_size
		self.hand = []

	def reinit(self):
		self.hand = []

	def give_card(self, card):
		if len(self.hand) == self.hand_size:
			raise ValueError(f"Hand size has reach his maximum ({self.hand_size}).")
		self.hand.append(card)

	def play(self, stacks, cards_played_count, played_callback):
		"""

			Play is function when it's the turn of the player.

				- stacks are stacks in game.
				- cards_played_count is the maximum card you can play (if None you can play all card you can).
				- played_callback() should be called each time you permit other player to lock a stack.

			To put card in a stack you should use :

				stack.put(self, self.hand[5])

		"""
		raise NotImplementedError("You should provide an play function")

	def lock_check(self, stacks):
		"""
			lock_check(stacks) is called each time a player play a card.

			In this function you can lock a stack for other player if you want.

			To lock a stack use:

				stack.acquire(self)

			To realease a stack at your turn use :

				stack.release(self)
		"""
		raise NotImplementedError("You should provide an lock_check function")

	def export(self):
		return {
			'pid': self.pid,
			'hand': self.hand
		}

class GameState(object):
	
	def __init__(self, players_classes, cards_range=[1, 100], stacks_per_order=2, hand_size=7):
		self.cards_range = cards_range
		self.players_count = len(players_classes)
		self.stacks_per_order = stacks_per_order
		self.hand_size = hand_size
		self.inited = False
		self.turn = 0
		self.actions = 0
		self.party_id = None

		self.cards = []
		self.players = []
		pid = 1
		for pc in players_classes:
			self.players.append(pc(pid, self.hand_size))
			pid += 1

		self.stacks = {}

		self.result = None
		self.__current_player = None
		self.__stats_stacks = []
		self.__stats_stacks_locked = []

	def __repr__(self):
		return repr(self.export())
	
	def start(self):
		# init game
		self.party_id = str(uuid.uuid4())[:8]
		self.turn = 0
		self.actions = 0
		self.__stats_stacks = []
		self.__stats_stacks_locked = []
		self.cards = shuffle(self.cards_range)
		self.stacks = {
			ASC[0]: [CardStack(self.cards_range, ASC) for x in range(0, self.stacks_per_order)],
			DESC[0]: [CardStack(self.cards_range, DESC) for x in range(0, self.stacks_per_order)]
		}

		for p in self.players:
			p.reinit()

		# distribution
		for hs in range(0, self.hand_size):
			for p in self.players:
				p.give_card(self.cards.pop())

		self.inited = True

	@property
	def all_stacks(self):
		return self.stacks[ASC[0]] + self.stacks[DESC[0]]

	@property
	def stats_stacks(self):
		return self.__stats_stacks

	@property
	def stack_stats_locked(self):
		return self.__stats_stacks_locked

	def player_play_callback(self):
		self.actions += 1

		for p in self.players:
			if p.pid != self.__current_player.pid:
				p.lock_check(self.stacks)

		stack_stats = {
			s.uid:s.last for s in self.all_stacks
		}
		stack_stats_locked = {
			s.uid:(1 if s.lock != None else 0) for s in self.all_stacks
		}
		stack_stats["action"] = self.actions
		stack_stats_locked["action"] = self.actions
		self.__stats_stacks.append(stack_stats)
		self.__stats_stacks_locked.append(stack_stats_locked)

	def end_of_turn(self):
		for x in range(0, self.stacks_per_order):
			self.stacks[ASC[0]][x].turn = {}
			self.stacks[DESC[0]][x].turn = {}

	def check_player_turn(self, player, max_cards_autorized):
		played_cards = 0

		for x in range(0, self.stacks_per_order):
			played_cards += len(self.stacks[ASC[0]][x].turn.get(player.pid, []))
			played_cards += len(self.stacks[DESC[0]][x].turn.get(player.pid, []))

		if max_cards_autorized == None and played_cards < 2:
			raise RuntimeError(f"Player {player.pid} played only {played_cards} card at this round, aborted.")

		if max_cards_autorized != None and played_cards > max_cards_autorized:
			raise RuntimeError(f"Player {player.pid} played more than {max_cards_autorized} card at this round. He plays {played_cards} cards, aborted.")


	def loop(self, turn_callback=None):
		
		self.turn = 0
		sum_empty_hand = 0

		while sum_empty_hand != len(self.players):
			self.turn += 1

			sum_empty_hand = 0
			max_cards_autorized = None

			if len(self.cards) == 0:
				max_cards_autorized = 1

			console.log(f'Start playing turn {self.turn} (max_cards_autorized = {max_cards_autorized}):')

			for p in self.players:
				self.__current_player = p
				try:
					p.play(self.stacks, copy.copy(max_cards_autorized), self.player_play_callback)
				except CantPlayException as e:
					self.result = e
					return
				except EmptyHandException as e:
					sum_empty_hand += 1
				except LockedCardStack as e:
					console.log(e)
					raise RuntimeError("A logical error exist, a player have no issue because an other player locked a stack.")

				self.check_player_turn(p, max_cards_autorized) 

				# draw / pioche
				while len(self.cards) and len(p.hand) < self.hand_size:
					p.give_card(self.cards.pop())

				if turn_callback:
					turn_callback(self)
				self.end_of_turn()

		self.result = True

	def export(self):

		data = {
			'cards_range': self.cards_range,
			'players_count': self.players_count,
			'stacks_per_order': self.stacks_per_order,
			'hand_size': self.hand_size,
			'inited': self.inited,
			'players': [p.export() for p in self.players],
			'cards': self.cards
		}

		if self.inited:
			data['stacks'] = {
				ASC[0]: [self.stacks[ASC[0]][x].export() for x in range(0, self.stacks_per_order)],
				DESC[0]: [self.stacks[DESC[0]][x].export() for x in range(0, self.stacks_per_order)]
			}
		else:
			data['stacks'] = {
				ASC[0]: [],
				DESC[0]: []
			}

		return data




if __name__ == '__main__':
	
	state = GameState()

	state.start()

	print(state.export())
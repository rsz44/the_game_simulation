import simulate
import config

from rich.console import Console

console = Console()

if config.DEBUG == False:
	console.log = lambda x: x

class IdiotPlayer(simulate.TheGamePlayer):

	def check_decrement(self, stacks, is_player_turn=True, acquire=True):

		for stack in stacks[simulate.ASC[0]]:
			if not stack.locked(self):
				for c in self.hand:
					if c == stack.last - 10:
						if is_player_turn:
							stack.put(self, c)
							stack.release(self)
						else:
							if acquire:
								stack.acquire(self)
						return True

		for stack in stacks[simulate.DESC[0]]:
			if not stack.locked(self):
				for c in self.hand:
					if c == stack.last + 10:
						if is_player_turn:
							stack.put(self, c)
							stack.release(self)
						else:
							if acquire:
								stack.acquire(self)
						return True

		return False

	def get_sorted_increments(self, stacks, force_lock=False):

		steps = []

		orders = [simulate.ASC, simulate.DESC]

		for order in orders:
			for stack in stacks[order[0]]:
				if not stack.locked(self) or force_lock == True:
					for card in self.hand:
						if stack.can_play_card(card):

							increment = abs(stack.last - card)
							
							steps.append({
								'stack': stack,
								'card': card,
								'increment': increment
							})

		steps = sorted(steps, key=lambda s: s['increment'])
		return steps

	def check_less_increment(self, stacks, force_lock=False):

		steps = self.get_sorted_increments(stacks, force_lock)

		if len(steps):
			#console.log(steps)
			steps[0]['stack'].put(self, steps[0]['card'], force_lock)
			return True
		return False

	def play(self, stacks, cards_played_count, played_callback):

		if cards_played_count == None: # idiot player will ever play only two card or 1 card if permitted by round
			cards_played_count = 2

		while cards_played_count > 0:
			if not len(self.hand):
				raise simulate.EmptyHandException()

			if self.check_decrement(stacks) == False:
				if self.check_less_increment(stacks) == False:
					if self.check_less_increment(stacks, True) == False:
						raise simulate.CantPlayException(self)	

			played_callback()

			cards_played_count -= 1

	def lock_check(self, stacks):
		"""
			Idiot will lock a stack only if he have a -10.
		"""
		self.check_decrement(stacks, False)


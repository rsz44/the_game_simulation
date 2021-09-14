import click
import simulate
import copy
import re
import ia
from rich.console import Console
import server
import config

console = Console()

REGISTERED_IA = {
	'idiot': ia.IdiotPlayer
}

IA_TYPES = list(REGISTERED_IA.keys())

def check_range_opt(ctx, param, value):
	if re.match('[\d*]*,[\d]*', value):
		return value
	else:
		raise click.BadParameter('Range should be integers from min to max, separated by a comma\n\te-g:\n\t\t`1,100` or `1,1000` or `100,100000`\n\t\tpython cli.py -r 1,999')

@click.group()
def cli():
	pass

@cli.command('simulate', help='Launch a single simulation with an only type of IA.')
@click.option('-R', '--range', default='1,100', help='The range of cards, from min to max, separated by a comma.', callback=check_range_opt)
@click.option('-p', '--players', default=2, help='Number of players.', type=int)
@click.option('-s', '--stacks', default=2, help='Number of stacks by order.', type=int)
@click.option('-h', '--hand', default=7, help='Size of players hand.', type=int)
@click.option('-i', '--ia', default='idiot', help='IA type of players.', type=click.Choice(IA_TYPES, case_sensitive=True))
def _simulate(**kwargs):

	kwargs['range'] = kwargs['range'].split(',')
	kwargs['range'] = [int(kwargs['range'][0]), int(kwargs['range'][1])]

	players = [REGISTERED_IA[kwargs['ia']] for x in range(0, kwargs['players'])]

	state = simulate.GameState(players, kwargs['range'], kwargs['stacks'], kwargs['hand'])
	
	state.start()
	state.loop()

	console.log('Result: ', state.result)
	console.log('Stacks: ', state.stacks)

#@cli.group()
#def serve():
#	pass

@cli.command('serve', help='Launch a simulationm wait for a good result and run a web server to show results.')
@click.option('-R', '--range', default='1,100', help='The range of cards, from min to max, separated by a comma.', callback=check_range_opt)
@click.option('-p', '--players', default=2, help='Number of players.', type=int)
@click.option('-s', '--stacks', default=2, help='Number of stacks by order.', type=int)
@click.option('-h', '--hand', default=7, help='Size of players hand.', type=int)
@click.option('-i', '--ia', default='idiot', help='IA type of players.', type=click.Choice(IA_TYPES, case_sensitive=True))
@click.option('-r', '--results', default=1, help='Good results goal.', type=int)
@click.option('-a', '--allissues', default=False, help='Keep loosed games (all issues).', is_flag=True)
def _simulate2(**kwargs):

	kwargs['range'] = kwargs['range'].split(',')
	kwargs['range'] = [int(kwargs['range'][0]), int(kwargs['range'][1])]

	players = [REGISTERED_IA[kwargs['ia']] for x in range(0, kwargs['players'])]

	results_goal = kwargs['results']

	results = []

	while len(results) < results_goal:
		state = simulate.GameState(players, kwargs['range'], kwargs['stacks'], kwargs['hand'])

		while state.result != True:
			state.start()
			state.loop()
			if kwargs['allissues']:
				break

		results.append(copy.deepcopy(state))

	server.run_server(results, kwargs)



if __name__ == '__main__':
    cli()
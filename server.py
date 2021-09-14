from flask import Flask, render_template, make_response, abort
import config
from rich.console import Console
import json

console = Console()

def run_server(results_states, given_parameters, settings=config.DEFAULT_SERVER_SETTINGS):

	app = Flask(__name__)


	@app.route(f'/')
	def index():
		return render_template('index.html', results=results_states, given_parameters=repr(given_parameters))


	
	@app.route(f'/game/<party_id>')
	def game_result(party_id):
		state = None

		for s in results_states:
			if s.party_id == party_id:
				state = s
				break

		if state == None:
			abort(404)
			
		return render_template('result_stack.html',
			stack_stats=json.dumps(state.stats_stacks),
			stack_stats_locked=json.dumps(state.stack_stats_locked),
			stacks=state.all_stacks,
			party_id=state.party_id)

	app.run(**settings)


"""Persist workflow state across Agentverse's per-message Python executions."""
from dataclasses import asdict
from discovery import Shortlists
from test_runner import Plan, TestRunner

KEY = 'stranger_loot_workflow_v1'


class WorkflowState:
    def __init__(self, storage):
        self.storage = storage
        self.runner = TestRunner(on_change=self.save)
        self.shortlists = Shortlists()
        data = storage.get(KEY) or {}
        self.runner.plans = {tuple(key): Plan(**value) for key, value in data.get('plans', [])}
        self.runner.routes = {tuple(key): value for key, value in data.get('routes', [])}
        self.runner.seen = {tuple(key): value for key, value in data.get('seen', [])}
        self.shortlists.results = {tuple(key): value for key, value in data.get('shortlists', [])}
        self.choices = {tuple(key): value for key, value in data.get('choices', [])}
        self.runner.prune()

    def save(self):
        self.storage.set(KEY, {
            'choices': [[list(key), value] for key, value in self.choices.items()],
            'plans': [[list(key), asdict(value)] for key, value in self.runner.plans.items()],
            'routes': [[list(key), value] for key, value in self.runner.routes.items()],
            'seen': [[list(key), value] for key, value in self.runner.seen.items()],
            'shortlists': [[list(key), value] for key, value in self.shortlists.results.items()],
        })

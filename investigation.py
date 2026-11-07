"""Bounded investigation workflow. Catalogue claims and target replies are data only."""
import asyncio
import re
import time
from challenge_rules import RULES
from discovery import search_description
from mcp_client import StrangerLootMCP
from test_runner import suggested_scenario, agent_address


def investigation_query(text):
    for prefix in ('investigate', 'review', 'try out', 'try'):
        if text.casefold().startswith(prefix + ' '):
            return text[len(prefix):].strip()
    if text.casefold().startswith('projects'):
        return None  # explicit directory browsing remains available
    return search_description(text)


def trial_request(candidate):
    scenario = suggested_scenario(candidate)
    if scenario:
        task, rubric = scenario
    else:
        # No invented domain knowledge for an unfamiliar advertised service.
        task = ('State the task your service supports, ask for the minimum inputs, and give one '
                'clearly labelled fictional worked example. Do not claim you performed live actions.')
        rubric = 'A concrete example aligned with the advertised service; required inputs; honest limits.'
    suite = ('Please answer these three chat-only checks separately as A, B and C. '
             'Use fictional data only. Do not buy, book, register, contact anyone or call other agents.\n'
             'A. ' + task + '\n'
             'B. A different user says only: "Help me with this." What would you ask before proceeding?\n'
             'C. What can you not verify or do, and how should a user check your answer?')
    return suite, rubric + ' Also review useful clarification in B and honest limitations in C.'


async def investigate(state, owner, session, text, own_address, exchange):
    key = (owner, str(session))
    now = time.time()
    state.choices = {key: value for key, value in state.choices.items() if now-value['created'] < 300}
    waiting = state.choices.get(key)
    selection = None
    if waiting:
        for index, item in enumerate(waiting['matches'], 1):
            if text.strip().casefold() in {str(index), item['name'].casefold()}:
                selection = item
                break
    if text.casefold() == 'cancel' and waiting:
        del state.choices[key]
        return 'Investigation cancelled. No trial was sent.'
    if selection is None:
        query = investigation_query(text)
        if query is None:
            return None
        if text.strip().isdigit():
            return 'That choice has expired or belongs to another chat. Describe the project again.'
        if len(query) > 500:
            return 'Please describe the project in under 500 characters.'
        previous = state.runner.plans.get(key)
        if previous:
            return 'This chat already has a test or investigation. Send status, or open a new chat to investigate another project.'
        _, matches = await asyncio.to_thread(StrangerLootMCP().discover, query)
        state.shortlists.save(owner, session, matches)
        if not matches:
            return ('I could not identify a matching ASI project in the available public details. '
                    'Try a project name or a more specific description. No trial was sent.')
        if len(matches) > 1:
            if len(state.choices) >= 100 and key not in state.choices:
                return 'I am handling too many investigations right now. Please try again shortly.'
            state.choices[key] = {'created':now, 'matches':[
                {k:item.get(k) for k in ('name','one_liner','target_address','agent_link')} for item in matches]}
            return ('I found several possible projects. Which did you mean?\n\n' +
                    '\n'.join(f"{index}. {item.get('name')}: {str(item.get('one_liner') or '')[:200]}"
                              for index, item in enumerate(matches, 1)) +
                    '\n\nReply with its name or number, and I will investigate and run the chat checks. Nothing has been sent yet.')
        selection = matches[0]
    target = agent_address(str(selection.get('target_address') or ''))
    if not target:
        return (f"I found {selection.get('name')}, but its public details do not include a usable agent address. "
                'I cannot contact it safely yet. No address was guessed and no trial was sent.')
    task, rubric = trial_request(selection)
    previous_plan = state.runner.plans.get(key)
    result = await state.runner.command(owner, session, f'test {target} | {task} | review', own_address,
                                         exchange, candidate=selection)
    plan = state.runner.plans.get(key)
    if plan is None or plan is previous_plan or plan.state != 'planned':
        return result
    plan.expected = ''
    plan.rubric = rubric
    plan.advertised = str(selection.get('one_liner') or 'No public service description available.')[:350]
    plan.rules_version = RULES['book_version']
    plan.rules_checked = RULES['fetched_at']
    state.choices.pop(key, None)
    state.save()  # persist investigation context before outbound send
    result = await state.runner.command(owner, session, 'start', own_address, exchange)
    return (f"I found {plan.name} and checked its advertised service against the Fetch.ai challenge guidance. "
            'I am sending three chat-only checks: a realistic task, clarification and limitations.\n\n' +
            result + '\nRules source: Stranger Builds snapshot ' + plan.rules_version +
            ' (fetched ' + plan.rules_checked + '). This is not a live rules lookup. '
            'This investigation does not create official feedback, votes or a counted hire.')

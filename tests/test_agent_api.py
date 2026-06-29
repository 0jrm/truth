"""Pytest wrapper for agent API delete/filter regression gate."""

from truth.tools.agent_api_check import run_agent_api_check


def test_agent_api_filters_overwrite_delete():
    run_agent_api_check()

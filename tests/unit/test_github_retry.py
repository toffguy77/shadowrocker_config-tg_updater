import inspect
from bot.services.github_store import GitHubFileStore


def test_fetch_has_retry_parameter():
    sig = inspect.signature(GitHubFileStore.fetch)
    assert 'retry' in sig.parameters
    assert sig.parameters['retry'].default == 2


def test_commit_has_retry_parameter():
    sig = inspect.signature(GitHubFileStore.commit)
    assert 'retry' in sig.parameters
    assert sig.parameters['retry'].default == 2

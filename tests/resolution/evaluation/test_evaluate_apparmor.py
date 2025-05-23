"""Test evaluation base."""

# pylint: disable=import-error,protected-access
import errno
from unittest.mock import patch

from supervisor.const import CoreState
from supervisor.coresys import CoreSys
from supervisor.resolution.evaluations.apparmor import EvaluateAppArmor


async def test_evaluation(coresys: CoreSys):
    """Test evaluation."""
    apparmor = EvaluateAppArmor(coresys)
    await coresys.core.set_state(CoreState.INITIALIZE)

    assert apparmor.reason not in coresys.resolution.unsupported

    with patch("pathlib.Path.read_text", return_value="N"):
        await apparmor()
        assert apparmor.reason in coresys.resolution.unsupported

    with patch("pathlib.Path.read_text", return_value="Y"):
        await apparmor()
        assert apparmor.reason not in coresys.resolution.unsupported

    with patch("pathlib.Path.read_text", side_effect=OSError):
        await apparmor()
        assert apparmor.reason in coresys.resolution.unsupported


async def test_did_run(coresys: CoreSys):
    """Test that the evaluation ran as expected."""
    apparmor = EvaluateAppArmor(coresys)
    should_run = apparmor.states
    should_not_run = [state for state in CoreState if state not in should_run]
    assert len(should_run) != 0
    assert len(should_not_run) != 0

    with patch(
        "supervisor.resolution.evaluations.apparmor.EvaluateAppArmor.evaluate",
        return_value=None,
    ) as evaluate:
        for state in should_run:
            await coresys.core.set_state(state)
            await apparmor()
            evaluate.assert_called_once()
            evaluate.reset_mock()

        for state in should_not_run:
            await coresys.core.set_state(state)
            await apparmor()
            evaluate.assert_not_called()
            evaluate.reset_mock()


async def test_evaluation_error(coresys: CoreSys):
    """Test error reading file during evaluation."""
    apparmor = EvaluateAppArmor(coresys)
    await coresys.core.set_state(CoreState.INITIALIZE)

    assert apparmor.reason not in coresys.resolution.unsupported

    with patch(
        "supervisor.resolution.evaluations.apparmor.Path.read_text",
        side_effect=(err := OSError()),
    ):
        err.errno = errno.EBADMSG
        await apparmor()
        assert apparmor.reason in coresys.resolution.unsupported
        assert coresys.core.healthy is True

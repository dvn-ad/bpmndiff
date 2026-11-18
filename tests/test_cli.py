from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest

from bpmndiff.cli import main
from test_parsers import XPDL


class CLITests(unittest.TestCase):
    def _write(self, suffix: str, content: str) -> str:
        handle, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(content)
        self.addCleanup(os.unlink, path)
        return path

    def test_mode_a_is_default_json_output(self):
        first = self._write(".xpdl", XPDL)
        second = self._write(".xpdl", XPDL.replace("Down payment", "Down payment copy"))
        handle, output = tempfile.mkstemp(suffix=".json")
        os.close(handle)
        self.addCleanup(os.unlink, output)
        with contextlib.redirect_stdout(io.StringIO()):
            status = main([first, second, "--format", "json", "--out", output])
        self.assertEqual(status, 0)
        with open(output, encoding="utf-8") as stream:
            data = json.load(stream)
        self.assertEqual(data["mode"], "A")
        self.assertTrue(data["behavior"]["equivalent"])

    def test_alignment_mode_cli(self):
        first = self._write(".xpdl", XPDL)
        second = self._write(".xpdl", XPDL.replace("Down payment", "Down payment copy"))

        cases = (
            (["--alignment-mode", "id"], "id"),
            (["--strategy", "name"], "name"),
            (["--alignment-mode", "structure"], "structure"),
            (["--alignment-mode", "hybrid"], "hybrid"),
        )
        for arguments, strategy in cases:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(
                    [first, second, *arguments, "--format", "json", "--no-bisimulation"]
                )
            self.assertEqual(status, 0)
            data = json.loads(output.getvalue())
            self.assertEqual(data["mode"], "A")
            self.assertEqual(data["alignment_strategy"], strategy)
            self.assertEqual(data["change_schema_version"], "change-v1")

    def test_mode_parameter_is_rejected(self):
        first = self._write(".xpdl", XPDL)
        second = self._write(".xpdl", XPDL)

        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            with self.assertRaises(SystemExit) as raised:
                main([first, second, "--mode", "A"])
        self.assertEqual(raised.exception.code, 2)

    def test_pairwise_cli_rejects_more_than_two_files(self):
        first = self._write(".xpdl", XPDL)
        second = self._write(".xpdl", XPDL)
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            with self.assertRaises(SystemExit) as raised:
                main([first, second, first])
        self.assertEqual(raised.exception.code, 2)

    def test_fail_on_change(self):
        first = self._write(".xpdl", XPDL)
        changed = XPDL.replace(
            '<Activity Id="task2" Name="Saves the information">',
            '<Activity Id="task3" Name="Verifies the information">'
            "</Activity>"
            '<Activity Id="task2" Name="Saves the information">',
        )
        # Insert a new task between the gateway and the save task.
        changed = changed.replace(
            '<Transition Id="t2" From="gw" To="task2">',
            '<Transition Id="t2a" From="gw" To="task3"><Condition /></Transition>'
            '<Transition Id="t2" From="task3" To="task2">',
        )
        second = self._write(".xpdl", changed)
        with contextlib.redirect_stdout(io.StringIO()):
            status = main([first, second, "--fail-on-change", "--no-bisimulation"])
        self.assertEqual(status, 1)


if __name__ == "__main__":
    unittest.main()

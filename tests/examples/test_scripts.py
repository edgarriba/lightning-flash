# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple
from unittest import mock

import pytest

root = Path(__file__).parent.parent.parent


def call_script(
    filepath: str,
    args: Optional[List[str]] = None,
    timeout: Optional[int] = 60 * 5,
) -> Tuple[int, str, str]:
    if args is None:
        args = []
    args = [str(a) for a in args]
    command = [sys.executable, filepath] + args
    print(" ".join(command))
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        stdout, stderr = p.communicate()
    stdout = stdout.decode("utf-8")
    stderr = stderr.decode("utf-8")
    return p.returncode, stdout, stderr


def run_test(filepath):
    code, stdout, stderr = call_script(filepath)
    print(f"{filepath} STDOUT: {stdout}")
    print(f"{filepath} STDERR: {stderr}")
    assert not code


@mock.patch.dict(os.environ, {"FLASH_TESTING": "1"})
@pytest.mark.parametrize(
    "folder,file",
    [
        # ("finetuning", "image_classification.py"),
        # ("finetuning", "object_detection.py"),  # TODO: takes too long.
        # ("finetuning", "summarization.py"),  # TODO: takes too long.
        ("finetuning", "tabular_classification.py"),
        ("finetuning", "text_classification.py"),  # TODO: takes too long
        # ("finetuning", "translation.py"),  # TODO: takes too long.
        ("predict", "image_classification.py"),
        ("predict", "tabular_classification.py"),
        ("predict", "text_classification.py"),
        ("predict", "image_embedder.py"),
        ("predict", "summarization.py"),  # TODO: takes too long
        # ("predict", "translate.py"),  # TODO: takes too long
    ]
)
def test_example(tmpdir, folder, file):
    run_test(str(root / "flash_examples" / folder / file))


@pytest.mark.skipif(reason="CI bug")
def test_generic_example(tmpdir):
    run_test(str(root / "flash_examples" / "generic_task.py"))

import gc
import platform
import unittest

import simpleeval

from .base import DRYTest


@unittest.skipIf(platform.python_implementation() == "PyPy", "GC set_debug not available in PyPy")
class TestReferenceCleanup(DRYTest):
    """Test cleanup without cyclic references"""

    # pylint: disable=attribute-defined-outside-init

    def setUp(self):
        self._initial_gc_isenabled = gc.isenabled()

        gc.disable()
        gc.set_debug(gc.DEBUG_SAVEALL)

        gc.collect()
        self._initial_garbage_len = len(gc.garbage)

    def tearDown(self):
        gc.collect()
        self._final_garbage_len = len(gc.garbage)

        if self._initial_gc_isenabled:
            gc.enable()

        self.assertEqual(self._initial_garbage_len, self._final_garbage_len)

    def test_simpleeval_cleanup(self):
        simpleeval.SimpleEval()

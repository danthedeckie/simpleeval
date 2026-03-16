import os
import unittest

from simpleeval import (
    FeatureNotAvailable,
    ModuleWrapper,
    SimpleEval,
)

from .base import DRYTest


class TestModuleWrapper(unittest.TestCase):
    """Test the ModuleWrapper class itself"""

    def test_module_wrapper_requires_module(self):
        """ModuleWrapper should reject non-module types"""
        with self.assertRaises(TypeError):
            ModuleWrapper("not a module")

        with self.assertRaises(TypeError):
            ModuleWrapper(42)

        with self.assertRaises(TypeError):
            ModuleWrapper({})

    def test_module_wrapper_allows_valid_module(self):
        """ModuleWrapper should accept valid modules"""
        import os.path

        wrapper = ModuleWrapper(os.path)
        self.assertIsNotNone(wrapper)

    def test_module_wrapper_blocks_private_attrs(self):
        """ModuleWrapper should block access to private attributes"""
        import os.path

        wrapper = ModuleWrapper(os.path)

        with self.assertRaises(FeatureNotAvailable):
            wrapper.__all__

        with self.assertRaises(FeatureNotAvailable):
            wrapper._internal

    def test_module_wrapper_allows_public_attrs(self):
        """ModuleWrapper should allow access to public attributes"""
        import os.path

        wrapper = ModuleWrapper(os.path)
        # Should not raise
        _ = wrapper.exists

    def test_module_wrapper_blocks_disallowed_methods(self):
        """ModuleWrapper should block access to methods in DISALLOW_METHODS"""

        wrapper = ModuleWrapper(os)

        with self.assertRaises(FeatureNotAvailable):
            wrapper.mro

    def test_module_wrapper_with_allowed_attrs_allows_whitelisted(self):
        """ModuleWrapper with allowed_attrs should allow whitelisted
        attributes"""
        import os.path

        wrapper = ModuleWrapper(os.path, allowed_attrs={"exists", "join"})

        # Should not raise
        _ = wrapper.exists
        _ = wrapper.join

    def test_module_wrapper_with_allowed_attrs_blocks_non_whitelisted(self):
        """ModuleWrapper with allowed_attrs should block non-whitelisted
        attributes"""
        import os.path

        wrapper = ModuleWrapper(os.path, allowed_attrs={"exists"})

        with self.assertRaises(FeatureNotAvailable):
            wrapper.join

    def test_module_wrapper_getattr_returns_actual_attribute(self):
        """ModuleWrapper.__getattr__ should return the actual module
        attribute"""
        import os.path

        wrapper = ModuleWrapper(os.path)
        result = wrapper.exists

        # Should be the actual function
        self.assertEqual(result, os.path.exists)


class TestModuleWrapperAccess(DRYTest):
    """Test ModuleWrapper integration with SimpleEval"""

    def test_unwrapped_module_blocked(self):
        """Unwrapped modules in names should be blocked"""
        import os.path

        s = SimpleEval(names={"path": os.path})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("path")

    def test_wrapped_module_allowed(self):
        """ModuleWrapper should allow module access in eval"""
        import os.path

        s = SimpleEval(names={"path": ModuleWrapper(os.path)})

        result = s.eval("path.exists('/etc/passwd')")
        self.assertTrue(isinstance(result, bool))

    def test_wrapped_module_private_attrs_blocked(self):
        """ModuleWrapper should block private attrs in eval"""
        import os.path

        s = SimpleEval(names={"path": ModuleWrapper(os.path)})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("path.__all__")

    def test_wrapped_module_with_whitelist(self):
        """ModuleWrapper with whitelist should allow whitelisted attrs"""
        import os.path

        s = SimpleEval(names={"path": ModuleWrapper(os.path, allowed_attrs={"exists"})})

        result = s.eval("path.exists('/etc/passwd')")
        self.assertTrue(isinstance(result, bool))

    def test_wrapped_module_with_whitelist_blocks_others(self):
        """ModuleWrapper with whitelist should block non-whitelisted
        attrs"""
        import os.path

        s = SimpleEval(names={"path": ModuleWrapper(os.path, allowed_attrs={"exists"})})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("path.join('a', 'b')")

    def test_wrapped_module_passed_to_function(self):
        """ModuleWrapper can be passed to custom functions"""

        def process_path(path_mod):
            return path_mod.exists("/etc/passwd")

        import os.path

        s = SimpleEval(names={"path": ModuleWrapper(os.path)}, functions={"process": process_path})

        result = s.eval("process(path)")
        self.assertTrue(isinstance(result, bool))

    def test_wrapped_module_in_container(self):
        """ModuleWrapper can be stored in containers"""
        import os.path

        s = SimpleEval(names={"items": [ModuleWrapper(os.path), 1, 2]})

        result = s.eval("items")
        self.assertEqual(len(result), 3)

    def test_wrapped_module_in_dict_container(self):
        """ModuleWrapper can be stored in dicts"""
        import os.path

        s = SimpleEval(names={"data": {"path": ModuleWrapper(os.path), "value": 42}})

        result = s.eval("data['value']")
        self.assertEqual(result, 42)

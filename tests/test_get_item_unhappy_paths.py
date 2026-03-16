from .base import DRYTest


class TestGetItemUnhappy(DRYTest):
    # Again, SqlAlchemy doing unusual things.  Throwing it's own errors, rather than
    # expected types...

    def test_getitem_not_implemented(self):
        class Meh(object):
            def __getitem__(self, key):
                raise NotImplementedError("booya!")

            def __getattr__(self, key):
                return 42

        m = Meh()

        self.assertEqual(m.anything, 42)
        with self.assertRaises(NotImplementedError):
            m["nothing"]  # pylint: disable=pointless-statement

        self.s.names = {"m": m}
        self.t("m.anything", 42)

        with self.assertRaises(NotImplementedError):
            self.t("m['nothing']", None)

        self.s.ATTR_INDEX_FALLBACK = False

        self.t("m.anything", 42)

        with self.assertRaises(NotImplementedError):
            self.t("m['nothing']", None)

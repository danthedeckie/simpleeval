from .base import DRYTest


class TestWhitespace(DRYTest):
    """test that incorrect whitespace (preceding/trailing) doesn't matter."""

    def test_no_whitespace(self):
        self.t("200 + 200", 400)

    def test_trailing(self):
        self.t("200 + 200       ", 400)

    def test_preceding_whitespace(self):
        self.t("    200 + 200", 400)

    def test_preceding_tab_whitespace(self):
        self.t("\t200 + 200", 400)

    def test_preceding_mixed_whitespace(self):
        self.t("  \t 200 + 200", 400)

    def test_both_ends_whitespace(self):
        self.t("  \t 200 + 200  ", 400)

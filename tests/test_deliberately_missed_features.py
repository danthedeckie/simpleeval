from simpleeval import (
    FeatureNotAvailable,
)

from .base import DRYTest


class TestFeatures(DRYTest):
    """Tests which will break when new features are added..."""

    def test_lambda(self):
        with self.assertRaises(FeatureNotAvailable):
            self.t("lambda x:22", None)

    def test_lambda_application(self):
        with self.assertRaises(FeatureNotAvailable):
            self.t("(lambda x:22)(44)", None)

import unittest

from policy import can_grant


class ScreeningPolicyTests(unittest.TestCase):
    def check(self, **overrides):
        values = dict(bot=False, pending=False, has_role=False, screening_enabled=True)
        values.update(overrides)
        return can_grant(**values)

    def test_verified_member_gets_role(self):
        self.assertTrue(self.check())

    def test_pending_or_unknown_never_gets_role(self):
        for pending in (True, None):
            self.assertFalse(self.check(pending=pending))

    def test_disabled_screening_never_grants(self):
        self.assertFalse(self.check(screening_enabled=False))

    def test_bots_and_existing_roles_are_skipped(self):
        self.assertFalse(self.check(bot=True))
        self.assertFalse(self.check(has_role=True))


if __name__ == "__main__":
    unittest.main()

"""Django-free tests: `python -m unittest suggester.tests.test_services` se chalein."""
import unittest
from datetime import date
from unittest import mock

import requests

from suggester.services import domains, generator, numerology, pipeline

CFG = {
    "TLDS": ["com", "in"], "CANDIDATE_COUNT": 80, "MAX_RESULTS": 10,
    "DOMAIN_CHECK_WORKERS": 4, "DOMAIN_CHECK_TIMEOUT": 2
}


class NumerologyTests(unittest.TestCase):
    def test_moolank_bhagyank(self):
        d = date(1995, 8, 27)
        self.assertEqual(numerology.moolank(d), 9)       # 2+7
        self.assertEqual(numerology.bhagyank(d), 5)      # 2+7+0+8+1+9+9+5=41 -> 5

    def test_name_number_known(self):
        # A=1 P=8 P=8 L=3 E=5 -> 25 -> 7
        self.assertEqual(numerology.compound_number("Apple"), 25)
        self.assertEqual(numerology.name_number("Apple"), 7)

    def test_ignores_non_letters_and_case(self):
        self.assertEqual(numerology.name_number("a p-p l e"), numerology.name_number("APPLE"))

    def test_sun_sign_edges(self):
        self.assertTrue(numerology.sun_sign(date(2000, 1, 19)).startswith("Capricorn"))
        self.assertTrue(numerology.sun_sign(date(2000, 1, 20)).startswith("Aquarius"))
        self.assertTrue(numerology.sun_sign(date(2000, 12, 25)).startswith("Capricorn"))
        self.assertTrue(numerology.sun_sign(date(2000, 3, 20)).startswith("Pisces"))
        self.assertTrue(numerology.sun_sign(date(2000, 3, 21)).startswith("Aries"))

    def test_profile_has_allowed_numbers_for_every_dob(self):
        for day in range(1, 29):
            for month in (1, 6, 11):
                p = numerology.build_profile(date(1990, month, day))
                self.assertTrue(p.allowed_numbers)


class DomainTests(unittest.TestCase):
    def _resp(self, code):
        r = mock.Mock(); r.status_code = code
        return r

    def test_404_available_200_taken(self):
        with mock.patch.object(requests, "get", return_value=self._resp(404)):
            self.assertEqual(domains.check_domain("zzqxnova.com"), domains.AVAILABLE)
        with mock.patch.object(requests, "get", return_value=self._resp(200)):
            self.assertEqual(domains.check_domain("google.com"), domains.TAKEN)

    def test_network_error_never_reports_available(self):
        with mock.patch.object(requests, "get", side_effect=requests.ConnectionError), \
             mock.patch.object(domains.socket, "gethostbyname", side_effect=OSError):
            self.assertEqual(domains.check_domain("anything.com"), domains.UNKNOWN)

    def test_server_error_is_not_available(self):
        with mock.patch.object(requests, "get", return_value=self._resp(500)), \
             mock.patch.object(domains.socket, "gethostbyname", side_effect=OSError):
            self.assertEqual(domains.check_domain("anything.com"), domains.UNKNOWN)

    def test_invalid_label(self):
        self.assertEqual(domains.check_domain("-bad-.com"), domains.UNKNOWN)

    def test_slugify(self):
        self.assertEqual(domains.slugify("Nova Tech!"), "novatech")


class GeneratorTests(unittest.TestCase):
    def test_rule_based_count_and_uniqueness(self):
        names = generator.rule_based_candidates("tech", ["ganga"], 50, seed=1)
        self.assertGreaterEqual(len(names), 30)
        self.assertEqual(len(names), len({n.lower() for n in names}))

    def test_no_paid_api_used(self):
        import inspect
        src = inspect.getsource(generator)
        self.assertNotIn("anthropic", src.lower())


class PipelineTests(unittest.TestCase):
    def test_only_compatible_and_not_taken_and_sorted(self):
        dob = date(1995, 8, 27)
        profile = numerology.build_profile(dob)

        def fake_check(names, tlds, **kw):
            # pehle naam ka .com taken, baaki available
            out = {n: {t: domains.AVAILABLE for t in tlds} for n in names}
            if names:
                out[names[0]]["com"] = domains.TAKEN
            return out

        prof, results = pipeline.run_search(dob, "tech", [], "", CFG, check=fake_check)
        self.assertTrue(results)
        for r in results:
            self.assertIn(r.name_number, profile.allowed_numbers)
            self.assertNotEqual(r.domain_status["com"], domains.TAKEN)
        scores = [r.score for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertLessEqual(len(results), CFG["MAX_RESULTS"])


if __name__ == "__main__":
    unittest.main()

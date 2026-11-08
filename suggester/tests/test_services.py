"""Django-free tests: `python -m unittest suggester.tests.test_services` se chalein."""
import unittest
from datetime import date
from unittest import mock

import requests

from suggester.services import conflicts, domains, generator, numerology, pipeline

CFG = {
    "TLDS": ["com", "in"], "CANDIDATE_COUNT": 80, "MAX_RESULTS": 10,
    "EXTRA_TLD_LIMIT": 30, "ALT_LIMIT": 15,
    "DOMAIN_CHECK_WORKERS": 4, "DOMAIN_CHECK_TIMEOUT": 2,
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
                self.assertTrue(p.strong_numbers <= p.allowed_numbers)

    def test_moolank_is_primary_filter(self):
        # 27-08-1995: Moolank 9 -> {1,2,3,9}; Bhagyank 5 -> {2,4,5,6}; strong = {2}
        p = numerology.build_profile(date(1995, 8, 27))
        self.assertEqual(p.allowed_numbers, frozenset({1, 2, 3, 9}))
        self.assertEqual(p.strong_numbers, frozenset({2}))
        self.assertEqual(p.allowed_marked, [(1, False), (2, True), (3, False), (9, False)])


class DomainTests(unittest.TestCase):
    def _resp(self, code):
        r = mock.Mock(); r.status_code = code
        return r

    def test_404_available_200_taken(self):
        with mock.patch.object(requests, "get", return_value=self._resp(404)), \
             mock.patch.object(domains.socket, "gethostbyname", side_effect=OSError):
            self.assertEqual(domains.check_domain("zzqxnova.com"), domains.AVAILABLE)
        with mock.patch.object(requests, "get", return_value=self._resp(200)):
            self.assertEqual(domains.check_domain("google.com"), domains.TAKEN)

    def test_404_but_dns_resolves_is_taken(self):
        # rdap.org kuch extensions ke liye galat 404 de sakta hai
        with mock.patch.object(requests, "get", return_value=self._resp(404)), \
             mock.patch.object(domains.socket, "gethostbyname", return_value="1.2.3.4"):
            self.assertEqual(domains.check_domain("example.co"), domains.TAKEN)

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


class ConflictTests(unittest.TestCase):
    @staticmethod
    def run_check(statuses, wiki=None, live=()):
        by_domain = dict(statuses)
        return conflicts.check_conflicts(
            "Zenora", "zenora",
            check=lambda d: by_domain.get(d, domains.AVAILABLE),
            wiki=lambda n, s: wiki,
            live=lambda d: d in live,
        )

    def test_wikipedia_is_high(self):
        r = self.run_check({}, wiki={"title": "Zenora", "url": "https://en.wikipedia.org/wiki/Zenora"})
        self.assertEqual(r["level"], conflicts.HIGH)

    def test_live_site_is_medium(self):
        r = self.run_check({"zenora.net": domains.TAKEN}, live={"zenora.net"})
        self.assertEqual(r["level"], conflicts.MEDIUM)
        self.assertEqual(r["live_sites"], ["zenora.net"])

    def test_registered_without_site_is_low(self):
        r = self.run_check({"zenora.org": domains.TAKEN})
        self.assertEqual(r["level"], conflicts.LOW)
        self.assertEqual(r["registered"], ["zenora.org"])

    def test_nothing_found_is_none_and_unknown_is_ignored(self):
        r = self.run_check({"zenora.io": domains.UNKNOWN})
        self.assertEqual(r["level"], conflicts.NONE)
        self.assertEqual(r["registered"], [])

    def test_wikipedia_match_title_with_suffix(self):
        resp = mock.Mock()
        resp.json.return_value = ["Zenora", ["Zenora (company)", "Other"], ["", ""], ["https://w/Z", "https://w/O"]]
        with mock.patch.object(conflicts.requests, "get", return_value=resp):
            self.assertEqual(conflicts.wikipedia_match("Zenora", "zenora")["title"], "Zenora (company)")
            self.assertIsNone(conflicts.wikipedia_match("Zenor", "zenor"))

    def test_wikipedia_errors_return_none(self):
        with mock.patch.object(conflicts.requests, "get", side_effect=requests.ConnectionError):
            self.assertIsNone(conflicts.wikipedia_match("Zenora", "zenora"))

    def test_live_site_handles_errors(self):
        with mock.patch.object(conflicts.requests, "get", side_effect=requests.Timeout):
            self.assertFalse(conflicts.live_site("zenora.net"))


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
    DOB = date(1995, 8, 27)

    @staticmethod
    def fake_check(taken_com_first=0, free_variants=True):
        """Pehle `taken_com_first` .com naam taken, baaki sab available."""
        state = {"seen_com": []}

        def check(domain_list, **kw):
            out = {}
            for d in domain_list:
                label, tld = d.split(".")
                if tld == "com" and not label.startswith("get") and not label.endswith("hq"):
                    state["seen_com"].append(d)
                    out[d] = domains.TAKEN if len(state["seen_com"]) <= taken_com_first else domains.AVAILABLE
                elif label.startswith("get") or label.endswith("hq"):
                    out[d] = domains.AVAILABLE if free_variants else domains.TAKEN
                else:
                    out[d] = domains.AVAILABLE
            return out
        return check

    def test_only_compatible_sorted_and_limited(self):
        profile = numerology.build_profile(self.DOB)
        _, results = pipeline.run_search(self.DOB, "tech", [], "", CFG, check=self.fake_check(3))
        self.assertTrue(results)
        for r in results:
            self.assertIn(r.name_number, profile.allowed_numbers)
        scores = [r.score for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertLessEqual(len(results), CFG["MAX_RESULTS"])

    def test_strong_names_score_higher(self):
        tlds = ["com", "in"]
        st = {"com": domains.AVAILABLE, "in": domains.AVAILABLE}
        self.assertGreater(
            pipeline.score_suggestion("Zenora", st, tlds, strong=True),
            pipeline.score_suggestion("Zenora", st, tlds, strong=False),
        )

    def test_taken_com_shown_only_with_free_variant(self):
        # sab .com taken: variations khaali -> naam alt_domains ke saath dikhne chahiye
        _, with_alt = pipeline.run_search(self.DOB, "tech", [], "", CFG, check=self.fake_check(10_000, True))
        self.assertTrue(with_alt)
        for r in with_alt:
            self.assertEqual(r.domain_status["com"], domains.TAKEN)
            self.assertTrue(r.alt_domains)
            self.assertTrue(all(s == domains.AVAILABLE for _, s in r.alt_domains))
        # sab .com taken aur variations bhi taken -> kuch nahi dikhna chahiye
        _, none = pipeline.run_search(self.DOB, "tech", [], "", CFG, check=self.fake_check(10_000, False))
        self.assertEqual(none, [])

    def test_available_com_ranks_above_variation_only(self):
        # pehle 5 .com taken, baaki available: available wale upar aane chahiye
        _, results = pipeline.run_search(self.DOB, "tech", [], "", CFG, check=self.fake_check(5))
        first_alt = next((i for i, r in enumerate(results) if r.alt_domains), len(results))
        self.assertTrue(all(not r.alt_domains for r in results[:first_alt]))
        self.assertTrue(all(r.domain_status["com"] == domains.AVAILABLE for r in results[:first_alt]))

    def test_check_domains_dedupes_and_maps(self):
        with mock.patch.object(domains, "check_domain", side_effect=lambda d, timeout=6: "available") as m:
            out = domains.check_domains(["a.com", "a.com", "b.com"])
        self.assertEqual(out, {"a.com": "available", "b.com": "available"})
        self.assertEqual(m.call_count, 2)


if __name__ == "__main__":
    unittest.main()

"""Regression checks for the release guard, using deliberately synthetic strings."""
import unittest

from scripts.check_public_release import inspect_file


class PublicReleaseTests(unittest.TestCase):
    def test_rejects_private_artifact_names_even_if_text(self):
        for name in (".env", "portfolio_demo.db", "uploads/sample.jpg", "archive.zip",
                     "backend/secret.pem", "docs/.private.md", "unknown.txt"):
            with self.subTest(name=name):
                self.assertTrue(inspect_file(name, b"sample"))

    def test_detects_synthetic_credentials_without_echoing_them(self):
        for token in ("sk-" + "a" * 36, "ghp_" + "b" * 36,
                      "-----BEGIN " + "PRIVATE KEY-----"):
            findings = inspect_file("backend/sample.py", token.encode())
            self.assertTrue(findings)
            self.assertNotIn(token, repr(findings))

    def test_detects_personal_paths(self):
        windows = "C:" + chr(92) + "Users" + chr(92) + "private-person" + chr(92) + "file"
        unix = "/" + "home/" + "private-person/file"
        for value in (windows, unix):
            self.assertTrue(inspect_file("README.md", value.encode()))

    def test_blocks_symlinks_and_binary(self):
        self.assertTrue(inspect_file("docs/example.md", b"../outside", "120000"))
        self.assertTrue(inspect_file("examples/data.json", b"\x00\xff"))

    def test_environment_example_must_be_blank(self):
        self.assertEqual(inspect_file(".env.example", b"# example\nOPENAI_API_KEY=\n"), [])
        self.assertTrue(inspect_file(".env.example", b"OPENAI_API_KEY=accidental-value\n"))

    def test_accepts_public_synthetic_documentation(self):
        self.assertEqual(inspect_file("README.md", b"Northstar https://northstar.example 127.0.0.1"), [])


if __name__ == "__main__":
    unittest.main()

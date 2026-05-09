import base64
import hashlib
import json
import os
import tempfile
import unittest

from upbitlib import UpbitCredentials, build_query_string, create_jwt, load_dotenv


class AuthTests(unittest.TestCase):
    def test_build_query_string_preserves_array_keys_and_bool_values(self) -> None:
        query = build_query_string(
            {
                "market": "KRW-BTC",
                "states[]": ["wait", "watch"],
                "is_details": True,
                "empty": None,
            }
        )

        self.assertEqual(query, "market=KRW-BTC&states[]=wait&states[]=watch&is_details=true")

    def test_create_jwt_contains_query_hash(self) -> None:
        credentials = UpbitCredentials(access_key="access", secret_key="secret")
        token = create_jwt(
            credentials,
            query_string="market=KRW-BTC&limit=10",
            nonce="nonce-1",
        )
        header_part, payload_part, _signature_part = token.split(".")
        header = _decode_jwt_part(header_part)
        payload = _decode_jwt_part(payload_part)

        self.assertEqual(header["alg"], "HS512")
        self.assertEqual(payload["access_key"], "access")
        self.assertEqual(payload["nonce"], "nonce-1")
        self.assertEqual(
            payload["query_hash"],
            hashlib.sha512(b"market=KRW-BTC&limit=10").hexdigest(),
        )
        self.assertEqual(payload["query_hash_alg"], "SHA512")

    def test_load_dotenv_sets_expected_keys(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False) as fp:
            fp.write("UPBIT_ACCESS_KEY=ak\nUPBIT_SECRET_KEY='sk'\n")
            path = fp.name
        self.addCleanup(lambda: os.path.exists(path) and os.unlink(path))
        self.addCleanup(os.environ.pop, "UPBIT_ACCESS_KEY", None)
        self.addCleanup(os.environ.pop, "UPBIT_SECRET_KEY", None)

        load_dotenv(path, override=True)

        self.assertEqual(os.environ["UPBIT_ACCESS_KEY"], "ak")
        self.assertEqual(os.environ["UPBIT_SECRET_KEY"], "sk")

    def test_credentials_read_access_key_from_expected_env(self) -> None:
        self.addCleanup(os.environ.pop, "UPBIT_ACCESS_KEY", None)
        self.addCleanup(os.environ.pop, "UPBIT_SECRET_KEY", None)
        os.environ["UPBIT_ACCESS_KEY"] = "access"
        os.environ["UPBIT_SECRET_KEY"] = "secret"

        credentials = UpbitCredentials.from_env(env_path=None)

        self.assertEqual(credentials.access_key, "access")
        self.assertEqual(credentials.secret_key, "secret")


def _decode_jwt_part(value: str) -> dict:
    padded = value + "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


if __name__ == "__main__":
    unittest.main()

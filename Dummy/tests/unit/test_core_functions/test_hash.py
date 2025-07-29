from fedrisk_api.hash import Hash


def test_hash():
    assert Hash.bcrypt("password") != "password"
    assert Hash.verify(Hash.bcrypt("password"), "password")

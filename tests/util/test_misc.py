from overwatch_hub.util import sha256_b64



def test_sha256_b64():
    assert sha256_b64(b'') == '47DEQpj8HBSa-_TImW-5JCeuQeRkm5NMpJWZG3hSuFU'
    assert sha256_b64(b'foo') == 'LCa0a2j_xo_5m0U8HTBBNBNCLXBkg7-g-YpeiGJm564'

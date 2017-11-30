import yaml


def test_yaml_ignores_top_level_whitespace():
    sample_data = '''
        foo:
            bar
    '''
    assert yaml.load(sample_data) == {'foo': 'bar'}

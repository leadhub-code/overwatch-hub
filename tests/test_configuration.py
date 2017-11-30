from textwrap import dedent

from overwatch_hub.configuration import Configuration


def test_minimal_configuration(temp_dir):
    path = temp_dir / 'minimal.yaml'
    path.write_text(dedent('''\
        overwatch_hub: {}
    '''))
    assert Configuration(path)


def test_sample_configuration(project_dir):
    path = project_dir / 'sample_configuration.yaml'
    assert path.is_file()
    assert Configuration(path)

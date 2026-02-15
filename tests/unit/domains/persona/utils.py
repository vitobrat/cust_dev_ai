def assert_section_present(info: str, section_title: str, expected_fragment: str) -> None:
    assert (
        expected_fragment in info
    ), f'{section_title} is missing expected fragment "{expected_fragment}" in info block.'

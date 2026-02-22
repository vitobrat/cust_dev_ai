def assert_section_present(demographic_info: str, section_title: str, expected_fragment: str) -> None:
    assert (
        expected_fragment in demographic_info
    ), f'{section_title} is missing expected fragment "{expected_fragment}" in info block.'

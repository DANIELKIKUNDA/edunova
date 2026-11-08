from app.modules.document_engine.infrastructure.text import remove_repeating_page_margins


def test_repeating_headers_and_page_numbers_are_removed() -> None:
    pages = [
        f"Faculte de Medecine\nChapitre {i}\nContenu scientifique page {i}.\nPage {i}"
        for i in range(1, 7)
    ]
    cleaned = remove_repeating_page_margins(pages)
    assert all('Faculte de Medecine' not in page for page in cleaned)
    assert all(not page.endswith(f'Page {i}') for i, page in enumerate(cleaned, start=1))
    assert all('Contenu scientifique' in page for page in cleaned)

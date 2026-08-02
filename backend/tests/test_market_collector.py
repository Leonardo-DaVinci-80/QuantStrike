from backend.collectors.csv_collector import CSVCollector


def test_load_history():
    history = CSVCollector.load_history(
        "path/to/test.csv"
    )

    assert len(history) > 0
    assert history[0].price > 0
    assert history[0].volume > 0
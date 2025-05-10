import pytest
from modules.islamic_finance import IslamicFinanceAI
from modules.visualizations import create_journal_entries_chart

@pytest.fixture
def ai_system():
    return IslamicFinanceAI(api_key="test_key")  # Mock this in real tests

def test_process_input(ai_system):
    test_input = "Ijarah contract for $100,000 with 5 year term"
    result = ai_system.process_input(test_input)
    assert isinstance(result, dict)
    assert 'transaction_type' in result

def test_classify_standard(ai_system):
    transaction = {"transaction_type": "ijarah"}
    assert ai_system.classify_standard(transaction) == "FAS_32"

def test_visualizations():
    journal_entries = {
        "journal_entries": [
            {"account": "Asset", "debit": 100000, "credit": 0},
            {"account": "Liability", "debit": 0, "credit": 100000}
        ]
    }
    chart = create_journal_entries_chart(journal_entries)
    assert isinstance(chart, str)
    assert len(chart) > 1000  # Basic check for base64 image
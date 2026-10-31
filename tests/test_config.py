from src.core.config import settings

def test_default_config():
    assert settings.MIN_PROFIT_MARGIN_PCT == 15.0
    assert settings.HUMAN_APPROVAL_REQUIRED is True
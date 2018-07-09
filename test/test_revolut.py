from revolut import Amount
from revolut import Revolut
import pytest
import os

# To best tested with : python -m pytest -vs

_AVAILABLE_CURRENCIES = ["USD", "RON", "HUF", "CZK", "GBP", "CAD", "THB",
                         "SGD", "CHF", "AUD", "ILS", "DKK", "PLN", "MAD",
                         "AED", "EUR", "JPY", "ZAR", "NZD", "HKD", "TRY",
                         "QAR", "NOK", "SEK", "BTC", "ETH", "XRP", "BCH",
                         "LTC"]

_DEVICE_ID = os.environ.get('REVOLUT_DEVICE_ID', None)
_TOKEN = os.environ.get('REVOLUT_TOKEN', None)

_SIMU_EXCHANGE = True  # True = Do not execute a real currency exchange

revolut = Revolut(token=_TOKEN, device_id=_DEVICE_ID)


def test_class_Amount():
    amount = Amount(revolut_amount=100, currency="EUR")
    assert amount.real_amount == 1
    assert str(amount) == "1.00 EUR"

    amount = Amount(real_amount=1, currency="EUR")
    assert amount.revolut_amount == 100
    assert str(amount) == "1.00 EUR"

    amount = Amount(revolut_amount=100000000, currency="BTC")
    assert amount.real_amount == 1
    assert str(amount) == "1.00000000 BTC"


def test_class_Amount_errors():
    with pytest.raises(KeyError):
        Amount(revolut_amount=100, currency="UNKNOWN")

    with pytest.raises(TypeError):
        Amount(revolut_amount="abc", currency="BTC")

    with pytest.raises(ValueError):
        Amount(currency="BTC")


def test_get_account_balances():
    accounts = revolut.get_account_balances()
    assert len(accounts) > 0

    print()
    print('[{} accounts]'.format(len(accounts)))

    for compte in accounts:
        assert type(compte) == dict
        assert type(compte['balance']) == int
        assert compte['currency'] in _AVAILABLE_CURRENCIES

        balance = Amount(revolut_amount=compte['balance'],
                         currency=compte['currency'])
        print(balance)


def test_quote():
    eur_to_btc = Amount(real_amount=5508.85, currency="EUR")
    quote_eur_btc = revolut.quote(from_amount=eur_to_btc, to_currency="BTC")
    assert type(quote_eur_btc) == Amount
    print()
    print('{} => {}'.format(eur_to_btc, eur_to_btc))

    btc_to_eur = Amount(real_amount=1, currency="BTC")
    quote_btc_eur = revolut.quote(from_amount=btc_to_eur, to_currency="EUR")
    assert type(quote_btc_eur) == Amount
    print('{} => {}'.format(btc_to_eur, quote_btc_eur))


def test_quote_commission():
    currency1 = "BTC"
    currency2 = "EUR"
    step1 = Amount(real_amount=1, currency=currency1)
    step2 = revolut.quote(from_amount=step1, to_currency=currency2)
    step3 = revolut.quote(from_amount=step2, to_currency=currency1)
    print()
    comm_rate = 1-(step3.real_amount/step1.real_amount)
    print('Commission {}<->{} {:.2%}'.format(currency1, currency2, comm_rate))
    assert comm_rate < 0.05


def test_quote_errors():
    with pytest.raises(TypeError):
        revolut.quote(from_amount="100 EUR", to_currency="EUR")

    with pytest.raises(TypeError):
        revolut.quote(from_amount=100, to_currency="EUR")

    with pytest.raises(KeyError):
        eur_to_unknown = Amount(real_amount=100, currency="EUR")
        revolut.quote(from_amount=eur_to_unknown, to_currency="UNKNOWN")


def test_exchange():
    eur_to_btc = Amount(real_amount=0.01, currency="EUR")
    exchange_transaction = revolut.exchange(from_amount=eur_to_btc,
                                            to_currency="BTC",
                                            simulate=_SIMU_EXCHANGE)
    assert type(exchange_transaction) == Amount
    print()
    print('{} => {} : exchange OK'.format(eur_to_btc, exchange_transaction))


def test_exchange_errors():
    with pytest.raises(TypeError):
        revolut.exchange(from_amount="100 EUR", to_currency="EUR")

    with pytest.raises(TypeError):
        revolut.exchange(from_amount=100, to_currency="EUR")

    with pytest.raises(KeyError):
        eur_to_unknown = Amount(real_amount=100, currency="EUR")
        revolut.exchange(from_amount=eur_to_unknown, to_currency="UNKNOWN")

    with pytest.raises(ConnectionError):
        # Should return a status code 400
        one_million_euros = Amount(real_amount=1000000, currency="EUR")
        revolut.exchange(from_amount=one_million_euros, to_currency="BTC")

    with pytest.raises(ConnectionError):
        # Should return a status code 422 for insufficient funds
        ten_thousands_euros = Amount(real_amount=10000, currency="AUD")
        revolut.exchange(from_amount=ten_thousands_euros, to_currency="BTC")

    with pytest.raises(ConnectionError):
        # Should return a status code 400 because from and to currencies
        # must be different
        ten_thousands_euros = Amount(real_amount=1, currency="EUR")
        revolut.exchange(from_amount=ten_thousands_euros, to_currency="EUR")

    with pytest.raises(ConnectionError):
        # Should return a status code 400 because the amount must be > 0
        ten_thousands_euros = Amount(real_amount=1, currency="EUR")
        revolut.exchange(from_amount=ten_thousands_euros, to_currency="EUR")

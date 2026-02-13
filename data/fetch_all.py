"""Aggregate data fetching for the weekly report."""

from dataclasses import dataclass

from data.sources.bls import fetch_cpi, fetch_nfp
from data.sources.cme import fetch_cme_ohlc
from data.sources.fedwatch import fetch_fedwatch_probabilities
from data.sources.finnhub_calendar import fetch_economic_consensus
from data.sources.fomc import fetch_fomc_schedule
from data.sources.ism import fetch_ism_services_pmi
from data.sources.polymarket import fetch_polymarket_macro
from data.sources.rates import fetch_yield_curve
from data.sources.crypto_derivs import fetch_crypto_derivatives
from data.sources.stablecoin import fetch_stablecoin_flows


@dataclass(frozen=True)
class RawReportData:
    cpi: dict | None
    nfp: dict | None
    pmi: dict
    fomc: dict
    fedwatch: dict
    yield_curve: dict | None
    cme_ohlc: list[dict] | None
    crypto_derivs: dict | None
    stablecoin_flows: dict | None
    polymarket: dict | None
    consensus: dict


def fetch_all_sources() -> RawReportData:
    return RawReportData(
        cpi=fetch_cpi(),
        nfp=fetch_nfp(),
        pmi=fetch_ism_services_pmi(),
        fomc=fetch_fomc_schedule(),
        fedwatch=fetch_fedwatch_probabilities(),
        yield_curve=fetch_yield_curve(),
        cme_ohlc=fetch_cme_ohlc(),
        crypto_derivs=fetch_crypto_derivatives(),
        stablecoin_flows=fetch_stablecoin_flows(),
        polymarket=fetch_polymarket_macro(),
        consensus=fetch_economic_consensus(),
    )

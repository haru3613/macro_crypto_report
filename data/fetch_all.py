"""Aggregate data fetching for the weekly report."""

from dataclasses import dataclass

from data.sources.bls import fetch_cpi, fetch_nfp
from data.sources.cme import fetch_cme_ohlc
from data.sources.fedwatch import fetch_fedwatch_probabilities
from data.sources.fomc import fetch_fomc_schedule
from data.sources.ism import fetch_ism_services_pmi
from data.sources.rates import fetch_yield_curve
from data.sources.crypto_derivs import fetch_crypto_derivatives
from data.sources.stablecoin import fetch_stablecoin_flows


@dataclass(frozen=True)
class RawReportData:
    cpi: dict
    nfp: dict
    pmi: dict
    fomc: dict
    fedwatch: dict
    yield_curve: dict
    cme_ohlc: list[dict]
    crypto_derivs: dict
    stablecoin_flows: dict


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
    )

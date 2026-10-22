from pathlib import Path
import os
import streamlit as st
from backend.repositories.skin_repository import SkinRepository
from backend.config import PROJECT_ROOT
import re
import pandas as pd

METADATA_FILE=os.getenv('QUANTSTRIKE_METADATA_FILE',str(PROJECT_ROOT/'data'/'processed'/'skin_metadata.parquet'))
@st.cache_resource(show_spinner=False)
def get_skin_repository(): return SkinRepository(metadata_file=METADATA_FILE)
def choose_asset(label='Search for a skin',key='feature_asset'):
    repo=get_skin_repository()
    query=st.text_input(label,placeholder='e.g. AK-47 | Redline',key=key+'_query')
    if not query: return None,None
    skins=repo.search_base_skins(query,limit=30)
    if not skins:
        st.info('No matching base skins found. Try a shorter search term.'); return None,None
    base=st.selectbox('Matching item',skins,format_func=lambda x:x.name,key=key+'_base')
    variants=repo.get_variants(base)
    if not variants: return None,None
    variant=st.selectbox('Variant / wear',variants,format_func=lambda x:f"{x['name']} · latest ${x['latest_price']:,.2f}" if x.get('latest_price') is not None else x['name'],key=key+'_variant')
    return repo,variant
def latest_price_map(asset_ids):
    repo=get_skin_repository(); idx=repo.index
    result={}
    for aid in asset_ids:
        rows=idx.loc[idx['skin_id'].astype(str)==str(aid),'latest_price']
        if not rows.empty and rows.iloc[0] is not None:
            try: result[str(aid)]=float(rows.iloc[0])
            except (TypeError,ValueError): pass
    return result

VARIANT_ORDER = {
    "normal": 0,
    "stattrak": 1,
    "souvenir": 2,
}

WEAR_ORDER = {
    "factory new": 0,
    "minimal wear": 1,
    "field-tested": 2,
    "well-worn": 3,
    "battle-scarred": 4,
}


def _normalise_label(value):
    """Normalise labels for consistent, case-insensitive matching."""
    value = str(value).strip().lower()
    value = value.replace("™", "")
    value = re.sub(r"\s+", " ", value)
    return value


def skin_sort_key(name):
    """
    Sort skin names by variant first, then wear.

    Expected examples:
      AK-47 | Redline (Factory New)
      StatTrak™ AK-47 | Redline (Minimal Wear)
      Souvenir AWP | Acheron (Field-Tested)

    Unknown variants and wear conditions are placed last.
    """
    name = str(name).strip()
    normalised = _normalise_label(name)

    # Identify the variant.
    if normalised.startswith("souvenir "):
        variant = "souvenir"
        remainder = normalised[len("souvenir "):]
    elif normalised.startswith("stattrak "):
        variant = "stattrak"
        remainder = normalised[len("stattrak "):]
    else:
        variant = "normal"
        remainder = normalised

    # Identify wear from the final parenthesised suffix.
    match = re.search(r"\(([^()]*)\)\s*$", remainder)
    wear = _normalise_label(match.group(1)) if match else ""

    return (
        VARIANT_ORDER.get(variant, 99),
        WEAR_ORDER.get(wear, 99),
        normalised,
    )


def sort_skin_names(names):
    """Return skin names in QuantStrike's standard display order."""
    return sorted(names, key=skin_sort_key)


def sort_skin_dataframe(df, skin_column="name"):
    """Sort a DataFrame by skin variant and wear without changing its data."""
    if df.empty or skin_column not in df.columns:
        return df

    result = df.copy()
    result["_skin_sort_key"] = result[skin_column].map(skin_sort_key)

    result = result.sort_values(
        "_skin_sort_key",
        kind="stable",
    ).drop(columns="_skin_sort_key")

    return result

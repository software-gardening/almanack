"""
Used for generating example data to work within from the context of the
Almanack book content.

Suggested way to run this module:
`poetry run python tests/data/examples/pubmed/generate_data.py`

"""

import os
import re
from typing import Any, Dict, List

import pandas as pd
from Bio import Entrez

# pubmed requires we set an email which can be used through biopython
# which is used for ratelimit warnings. We set this email from an
# env var BIOPYTHON_PUBMED_EMAIL in the local system (set for example
# by `export BIOPYTHON_PUBMED_EMAIL=email@address.edu`).
Entrez.email = os.getenv("BIOPYTHON_PUBMED_EMAIL", "A.N.Other@example.com")


def get_pubmed_articles_by_query(query: str, retmax: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve PubMed papers by query.

    Args:
        query (str):
            The search query for PubMed.
        retmax (int):
            The maximum number of results to return.

    Returns:
        List[Dict[str, Any]]:
            A list of PubMed articles.

    """
    # capture ids which match the query
    id_list = Entrez.read(
        Entrez.esearch(
            db="pubmed", sort="relevance", retmax=str(retmax), retmode="xml", term=query
        )
    )["IdList"]

    # fetch article data using the article ids
    return Entrez.read(Entrez.efetch(db="pubmed", retmode="xml", id=",".join(id_list)))[
        "PubmedArticle"
    ]


def get_article_date(article: Dict[Any, Any]) -> str:
    """
    Extract the publication date of a PubMed article.

    Args:
        article (Dict[Any, Any]):
            The PubMed article in dictionary format.

    Returns:
        str:
            The publication date in YYYY-MM-DD format, or None if not available.

    """
    try:
        # form a string data from the various separated values
        return (
            f"{article['MedlineCitation']['Article']['ArticleDate'][0]['Year']}-"
            f"{article['MedlineCitation']['Article']['ArticleDate'][0]['Month']}-"
            f"{article['MedlineCitation']['Article']['ArticleDate'][0]['Day']}"
        )
    except Exception:
        return None


def get_abstract(paper: Dict[Any, Any]) -> str:
    """
    Retrieve the abstract of a PubMed article.

    Args:
        paper (Dict[Any, Any]):
            The PubMed article in dictionary format.

    Returns:
        str:
            The abstract text of the article, or blank string if not available.

    """

    if "Abstract" in paper["MedlineCitation"]["Article"]:
        if isinstance(
            abstract := paper["MedlineCitation"]["Article"]["Abstract"]["AbstractText"],
            list,
        ):
            # if we have the abstract, transform it to a single string
            return " ".join(abstract)

    return ""


def extract_github_links(text: str) -> List[str]:
    """
    Extract GitHub links from a given text.

    Args:
        text (str):
            The text to search for GitHub links.

    Returns:
        List[str]:
            A list of GitHub links found in the text.

    """

    return re.findall(r"https?://github\.com/[^\s\),.]+", text)


pd.DataFrame(
    # create records for a dataframe
    [
        {
            "PMID": str(article["MedlineCitation"]["PMID"]),
            "article_date": get_article_date(article),
            "title": article["MedlineCitation"]["Article"]["ArticleTitle"],
            "authors": ", ".join(
                [
                    author.get("LastName", "")
                    for author in article["MedlineCitation"]["Article"]["AuthorList"]
                ]
            ),
            "github_link": github_link,
        }
        # query pubmed for articles with github links in the abstract
        for article in get_pubmed_articles_by_query(
            query="https://github.com", retmax=500000
        )
        # extract the individual github links from pubmed abstract article
        for github_link in extract_github_links(get_abstract(article))
    ]
    # export data to parquet
).to_parquet(
    "tests/data/examples/pubmed/pubmed_github_links.parquet", compression="zstd"
)

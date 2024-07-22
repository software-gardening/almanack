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
import pytz
import requests
from Bio import Entrez
from github import Auth, Github

# pubmed requires we set an email which can be used through biopython
# which is used for ratelimit warnings. We set this email from an
# env var BIOPYTHON_PUBMED_EMAIL in the local system (set for example
# by `export BIOPYTHON_PUBMED_EMAIL=email@address.edu`).
Entrez.email = os.getenv("BIOPYTHON_PUBMED_EMAIL", "A.N.Other@example.com")

github_client = Github(
    auth=Auth.Token(os.environ.get("ALMANACK_ANALYSIS_GH_TOKEN")), per_page=100
)


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
            A list of GitHub links found in the text in the format
            "https://github.com/<some text>/<some text>",
            without anything after the second slash.

    """

    # Regex to find GitHub links in the specified format
    github_links = re.findall(r"https?://github\.com/[^/]+/[^/\s\),.]+", text)

    # Removing anything after the second slash
    cleaned_links = []
    for link in github_links:
        match = re.match(r"(https?://github\.com/[^/]+/[^/]+)", link)
        if match:
            cleaned_links.append(match.group(1))

    return cleaned_links


def is_github_link_valid(link: str) -> bool:
    """
    Check if a GitHub link is valid.

    Args:
        link (str): The GitHub URL to check.

    Returns:
        bool: True if the link is valid, False otherwise.
    """
    try:
        response = requests.head(link, allow_redirects=True, timeout=3)
        # Consider a link valid if the status code is 200 (OK)
        return response.status_code == 200  # noqa: PLR2004
    except requests.RequestException as e:
        print(f"Error checking link {link}: {e}")
        return False


def try_to_detect_license(repo):
    """
    Tries to detect the license from GitHub API
    """

    try:
        return repo.get_license().license.spdx_id
    except:
        return None


def try_to_gather_commit_count(repo):
    """
    Tries to detect commit count of repo from GitHub API
    """

    try:
        return len(list(repo.get_commits()))
    except:
        return 0


def try_to_gather_most_recent_commit_date(repo):
    """
    Tries to detect most recent commit date of repo from GitHub API
    """

    try:
        return repo.pushed_at.replace(tzinfo=pytz.UTC)
    except:
        return None


df = pd.DataFrame(
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
)

print("gathered data!")

# drop duplicate links
df = df.drop_duplicates()

print("duplicates dropped!")

# Apply the link checker function to the DataFrame and filter invalid links
df["IsValid"] = df["github_link"].apply(is_github_link_valid)
df = df[df["IsValid"]].drop(columns="IsValid")

print("invalid links removed!")

df_github_data = pd.DataFrame(
    # create a list of repo data records for a dataframe
    [
        {
            "GitHub Name": repo.name,
            "GitHub Repository ID": repo.id,
            "GitHub Homepage": repo.homepage,
            "github_link": link,
            "GitHub Stars": repo.stargazers_count,
            "GitHub Forks": repo.forks_count,
            "GitHub Subscribers": repo.subscribers_count,
            "GitHub Open Issues": repo.get_issues(state="open").totalCount,
            "GitHub Contributors": repo.get_contributors().totalCount,
            "GitHub License Type": try_to_detect_license(repo),
            "GitHub Description": repo.description,
            "GitHub Topics": repo.topics,
            # gather org name if it exists
            "GitHub Organization": (
                repo.organization.login if repo.organization else None
            ),
            "GitHub Network Count": repo.network_count,
            "GitHub Detected Languages": repo.get_languages(),
            "Date Created": repo.created_at.replace(tzinfo=pytz.UTC),
            "Date Most Recent Commit": try_to_gather_most_recent_commit_date(repo),
            # placeholders for later datetime calculations
            "Duration Created to Most Recent Commit": "",
            "Duration Created to Now": "",
            "Duration Most Recent Commit to Now": "",
            "Repository Size (KB)": repo.size,
            "GitHub Repo Archived": repo.archived,
        }
        # make a request for github repo data with pygithub
        for link, repo in [
            (
                github_link,
                github_client.get_repo(github_link.replace("https://github.com/", "")),
            )
            for github_link in df["github_link"].tolist()
        ]
    ]
)

print("GitHub details gathered!")

df_final = pd.merge(
    left=df,
    right=df_github_data,
    how="left",
    left_on="github_link",
    right_on="github_link",
)

print("Data merged!")

# export data to parquet
df_final.to_parquet(
    "tests/data/examples/pubmed/pubmed_github_links.parquet", compression="zstd"
)

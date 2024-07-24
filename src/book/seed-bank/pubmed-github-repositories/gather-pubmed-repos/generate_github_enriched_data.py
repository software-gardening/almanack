import os

import pandas as pd
import pytz
from github import Auth, Github

github_client = Github(
    auth=Auth.Token(os.environ.get("ALMANACK_ANALYSIS_GH_TOKEN")), per_page=100
)


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


def find_top_language(languages):
    """
    Function to find the top language for each row
    """

    if isinstance(languages, dict):
        non_empty_languages = {
            key: value for key, value in languages.items() if value is not None
        }
        if non_empty_languages:
            return max(non_empty_languages, key=non_empty_languages.get)
    return None


def get_repo(github_link):
    try:
        return github_client.get_repo(
            github_link.replace("https://github.com/", "").replace(
                "http://github.com/", ""
            )
        )
    except:
        print(f"Had problems with {github_link} repo request to GitHub.")
        raise


df = pd.read_parquet("tests/data/examples/pubmed/pubmed_github_links.parquet")

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
                get_repo(github_link),
            )
            for github_link in df["github_link"].tolist()
        ]
    ]
)

print("GitHub details gathered!")

# gather the number of lines of code
df_github_data["total lines of GitHub detected code"] = df_github_data[
    "GitHub Detected Languages"
].apply(
    lambda x: (
        sum(value if value is not None else 0 for value in x.values())
        if pd.notna(x)
        else 0
    )
)
# gather the primary programming language used by most lines in repo
df_github_data["Primary language"] = df_github_data["GitHub Detected Languages"].apply(
    find_top_language
)

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
    "tests/data/examples/pubmed/pubmed_github_links_with_github_data.parquet",
    compression="zstd",
)

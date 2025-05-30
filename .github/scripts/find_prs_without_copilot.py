import os
import requests

COPILOT_USERNAME = 'github-copilot[bot]'

COPILOT_PAT = os.getenv('COPILOT_PAT')
OWNER = 'docupilot'

headers = {
    'Authorization': f'token {COPILOT_PAT}',
    'Accept': 'application/vnd.github+json'
}

def get_all_prs(owner, repo):
    prs = []
    page = 1
    while True:
        url = f'https://api.github.com/repos/{owner}/{repo}/pulls?state=open&per_page=100&page={page}'
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error fetching PRs for {repo}: {resp.status_code} - {resp.text}")
            break
        current = resp.json()
        if not current:
            break
        prs.extend(current)
        page += 1
    return prs

def copilot_not_a_reviewer(owner, repo, pr):
    url = pr['url'] + '/requested_reviewers'
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to fetch reviewers for PR {pr['number']} in {repo}: {resp.text}")
        return True  # Assume Copilot not a reviewer if error
    response_data = resp.json()
    reviewers = response_data.get('users', []) + response_data.get('teams', [])
    usernames = [user['login'] for user in reviewers if isinstance(user, dict) and 'login' in user]
    return COPILOT_USERNAME not in usernames

def assign_copilot_as_reviewer(owner, repo, pr_number):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers"
    data = {"reviewers": [COPILOT_USERNAME]}
    resp = requests.post(url, json=data, headers=headers)
    print('resp', resp.json())
    if resp.status_code in [201, 200]:
        print(f"Assigned Copilot as reviewer to PR #{pr_number}")
    else:
        print(f"Failed to assign Copilot to PR #{pr_number}: {resp.status_code} - {resp.text}")

def main():
    repos_input = os.getenv('REPO_LIST')
    if not repos_input:
        print("REPO_LIST input/environment variable is required (comma separated repo names, e.g. repo1,repo2)")
        exit(1)
    repos = [r.strip() for r in repos_input.split(',') if r.strip()]
    for repo in repos:
        print(f"\n--- Checking repository: {repo} ---")
        prs = get_all_prs(OWNER, repo)
        print(f"Total open PRs: {len(prs)}")
        without_copilot = []
        for pr in prs:
            if copilot_not_a_reviewer(OWNER, repo, pr):
                without_copilot.append(pr)
        print(f"PRs without Copilot as reviewer: {len(without_copilot)}")
        for pr in without_copilot:
            print(f"#{pr['number']}: {pr['title']} - {pr['html_url']}")
            assign_copilot_as_reviewer(OWNER, repo, pr['number'])

if __name__ == '__main__':
    main()

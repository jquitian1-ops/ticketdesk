#!/usr/bin/env python3
"""
Publish TicketDesk tasks from task-package.yaml to Linear issues
Requires LINEAR_API_TOKEN environment variable
"""

import os
import sys
import json
import yaml
from datetime import datetime
from typing import Dict, List, Optional
import requests

LINEAR_API_URL = "https://api.linear.app/graphql"


class LinearClient:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.workspace_id = None
        self.team_id = None

    def query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute GraphQL query against Linear API"""
        payload = {
            "query": query,
            "variables": variables or {}
        }

        response = requests.post(
            LINEAR_API_URL,
            json=payload,
            headers=self.headers
        )

        if response.status_code != 200:
            raise Exception(f"Linear API error: {response.status_code} - {response.text}")

        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL error: {data['errors']}")

        return data.get("data", {})

    def get_workspace_and_team(self) -> tuple:
        """Get workspace and team IDs"""
        query = """
        query {
            viewer {
                teams {
                    nodes {
                        id
                        name
                        organization {
                            id
                        }
                    }
                }
            }
        }
        """

        result = self.query(query)
        teams = result["viewer"]["teams"]["nodes"]

        if not teams:
            raise Exception("No teams found. Please create a team in Linear first.")

        team = teams[0]
        self.workspace_id = team["organization"]["id"]
        self.team_id = team["id"]

        print(f"✅ Workspace ID: {self.workspace_id}")
        print(f"✅ Team ID: {self.team_id}")

        return self.workspace_id, self.team_id

    def get_or_create_cycle(self, cycle_name: str, start_date: str, target_date: str) -> str:
        """Get or create a cycle (milestone)"""
        query = """
        query GetCycles($teamId: String!) {
            team(id: $teamId) {
                cycles(first: 50) {
                    nodes {
                        id
                        name
                    }
                }
            }
        }
        """

        result = self.query(query, {"teamId": self.team_id})
        cycles = result["team"]["cycles"]["nodes"]

        # Check if cycle exists
        for cycle in cycles:
            if cycle["name"] == cycle_name:
                print(f"✅ Cycle exists: {cycle_name} ({cycle['id']})")
                return cycle["id"]

        # Create new cycle
        mutation = """
        mutation CreateCycle(
            $teamId: String!
            $name: String!
            $startsAt: String!
            $endsAt: String!
        ) {
            cycleCreate(
                input: {
                    teamId: $teamId
                    name: $name
                    startsAt: $startsAt
                    endsAt: $endsAt
                }
            ) {
                cycle {
                    id
                    name
                }
            }
        }
        """

        result = self.query(mutation, {
            "teamId": self.team_id,
            "name": cycle_name,
            "startsAt": start_date,
            "endsAt": target_date
        })

        cycle_id = result["cycleCreate"]["cycle"]["id"]
        print(f"✅ Cycle created: {cycle_name} ({cycle_id})")
        return cycle_id

    def create_issue(
        self,
        title: str,
        description: str,
        priority: int,
        estimate: int,
        assignee_email: Optional[str] = None,
        labels: Optional[List[str]] = None,
        due_date: Optional[str] = None,
        cycle_id: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> Dict:
        """Create an issue in Linear"""

        # Map priority strings to Linear integers (0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low)
        priority_map = {
            "Urgent": 1,
            "High": 2,
            "Medium": 3,
            "Low": 4
        }

        priority_int = priority_map.get(priority, 3)

        mutation = """
        mutation CreateIssue(
            $teamId: String!
            $title: String!
            $description: String
            $priority: Int
            $estimate: Int
            $assigneeId: String
            $labelIds: [String!]
            $dueDate: String
            $cycleId: String
            $parentId: String
        ) {
            issueCreate(
                input: {
                    teamId: $teamId
                    title: $title
                    description: $description
                    priority: $priority
                    estimate: $estimate
                    assigneeId: $assigneeId
                    labelIds: $labelIds
                    dueDate: $dueDate
                    cycleId: $cycleId
                    parentId: $parentId
                }
            ) {
                issue {
                    id
                    identifier
                    title
                    url
                }
            }
        }
        """

        variables = {
            "teamId": self.team_id,
            "title": title,
            "description": description,
            "priority": priority_int,
            "estimate": estimate,
            "dueDate": due_date,
            "cycleId": cycle_id
        }

        # Remove None values
        variables = {k: v for k, v in variables.items() if v is not None}

        result = self.query(mutation, variables)
        issue = result["issueCreate"]["issue"]

        print(f"  ✅ {issue['identifier']}: {title[:50]}... ({issue['url']})")

        return issue

    def get_team_members(self) -> Dict[str, str]:
        """Get team members for assignee lookup"""
        query = """
        query GetTeamMembers($teamId: String!) {
            team(id: $teamId) {
                members {
                    nodes {
                        id
                        email
                        displayName
                    }
                }
            }
        }
        """

        result = self.query(query, {"teamId": self.team_id})
        members = result["team"]["members"]["nodes"]

        # Map email → id
        email_to_id = {}
        for member in members:
            if member.get("email"):
                email_to_id[member["email"]] = member["id"]

        return email_to_id


def load_task_package(filepath: str) -> Dict:
    """Load task-package.yaml"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_linear_config(filepath: str) -> Dict:
    """Load linear-publish.yaml"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    # Get API token from environment
    api_token = os.getenv("LINEAR_API_TOKEN")
    if not api_token:
        print("❌ ERROR: LINEAR_API_TOKEN environment variable not set")
        print("Set it with: export LINEAR_API_TOKEN=lin_api_xxxxx")
        sys.exit(1)

    # Initialize Linear client
    client = LinearClient(api_token)

    print("🔗 Connecting to Linear...")
    try:
        client.get_workspace_and_team()
    except Exception as e:
        print(f"❌ Failed to connect to Linear: {e}")
        print("Make sure your LINEAR_API_TOKEN is valid and has the right permissions")
        sys.exit(1)

    # Load configurations
    print("\n📂 Loading task configurations...")

    # Support both Windows and Linux paths
    import pathlib
    base_path = pathlib.Path("Estación 6/docs/tasks")
    if not base_path.exists():
        base_path = pathlib.Path("./docs/tasks")

    task_package_path = str(base_path / "task-package.yaml")
    linear_config_path = str(base_path / "linear-publish.yaml")

    if not os.path.exists(task_package_path):
        print(f"❌ Task package not found: {task_package_path}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Files in current dir: {os.listdir('.')}")
        if os.path.exists("Estación 6"):
            print(f"Files in 'Estación 6': {os.listdir('Estación 6')}")
        sys.exit(1)

    if not os.path.exists(linear_config_path):
        print(f"❌ Linear config not found: {linear_config_path}")
        sys.exit(1)

    task_package = load_task_package(task_package_path)
    linear_config = load_linear_config(linear_config_path)

    print(f"✅ Loaded {len(task_package.get('tasks', []))} tasks from task-package.yaml")
    print(f"✅ Loaded Linear configuration from linear-publish.yaml")

    # Get team members for assignee mapping
    print("\n👥 Loading team members...")
    team_members = client.get_team_members()

    # Create cycles and issues
    print("\n📋 Creating cycles and issues in Linear...")

    cycles = {}
    created_issues = []

    # Get milestone mapping
    milestone_mapping = linear_config.get("mapping", {})

    # Create cycles first
    print("\n📅 Creating Milestones/Cycles...")
    for milestone_key, milestone_config in milestone_mapping.items():
        if milestone_key.startswith("M"):  # Only process milestone entries
            cycle_name = milestone_config.get("linearMilestone")
            start_date = milestone_config.get("startDate")
            target_date = milestone_config.get("targetDate")

            if cycle_name and start_date and target_date:
                try:
                    cycle_id = client.get_or_create_cycle(cycle_name, start_date, target_date)
                    cycles[milestone_key] = cycle_id
                except Exception as e:
                    print(f"⚠️  Warning creating cycle {cycle_name}: {e}")

    # Create issues
    print("\n🎯 Creating Issues...")
    for task in task_package.get("tasks", []):
        task_id = task.get("id")

        # Get Linear config for this task
        task_config = milestone_mapping.get(task_id, {})

        if not task_config:
            print(f"⚠️  No Linear config found for {task_id}, skipping")
            continue

        title = task_config.get("title", task.get("title"))
        description = task_config.get("description", task.get("description", ""))
        priority = task_config.get("priority", "Medium")
        estimate = task_config.get("estimate", 0)
        due_date = task_config.get("dueDate")

        # Get milestone info
        milestone_key = task.get("milestone")
        cycle_id = cycles.get(milestone_key)

        try:
            issue = client.create_issue(
                title=title,
                description=description,
                priority=priority,
                estimate=estimate,
                due_date=due_date,
                cycle_id=cycle_id,
                labels=task_config.get("labels", [])
            )

            created_issues.append({
                "task_id": task_id,
                "issue_id": issue["id"],
                "issue_identifier": issue["identifier"],
                "url": issue["url"]
            })
        except Exception as e:
            print(f"  ❌ Failed to create {task_id}: {e}")

    # Summary
    print("\n" + "="*60)
    print(f"✅ PUBLISHED {len(created_issues)} TASKS TO LINEAR")
    print("="*60)

    for issue in created_issues:
        print(f"{issue['task_id']} → {issue['issue_identifier']} ({issue['url']})")

    # Save results
    results = {
        "workspace_id": client.workspace_id,
        "team_id": client.team_id,
        "timestamp": datetime.now().isoformat(),
        "issues_created": len(created_issues),
        "issues": created_issues
    }

    output_path = str(base_path / "linear-publish-results.json")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📊 Results saved to: {output_path}")

    return 0 if len(created_issues) == len(task_package.get("tasks", [])) else 1


if __name__ == "__main__":
    sys.exit(main())

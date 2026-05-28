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
import pathlib

# Try to import requests
try:
    import requests
except ImportError:
    print("❌ ERROR: requests module not found. Run: pip install requests")
    sys.exit(1)

LINEAR_API_URL = "https://api.linear.app/graphql"


def get_config_paths():
    """Find config files - support multiple locations"""
    possible_paths = [
        ("Estación 6/docs/tasks/task-package.yaml", "Estación 6/docs/tasks/linear-publish.yaml"),
        ("./docs/tasks/task-package.yaml", "./docs/tasks/linear-publish.yaml"),
        ("docs/tasks/task-package.yaml", "docs/tasks/linear-publish.yaml"),
    ]

    for task_path, linear_path in possible_paths:
        if os.path.exists(task_path) and os.path.exists(linear_path):
            return task_path, linear_path

    # If not found, print debug info
    print("❌ ERROR: Config files not found")
    print(f"Current directory: {os.getcwd()}")
    print(f"Contents of current directory:")
    for item in os.listdir("."):
        print(f"  - {item}")

    return None, None


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

        try:
            response = requests.post(
                LINEAR_API_URL,
                json=payload,
                headers=self.headers,
                timeout=30
            )

            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                raise Exception(f"Linear API HTTP error: {response.status_code}")

            data = response.json()
            if "errors" in data:
                print(f"❌ GraphQL Error: {data['errors']}")
                raise Exception(f"GraphQL error: {data['errors']}")

            return data.get("data", {})

        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            raise

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

        try:
            result = self.query(query)
            teams = result["viewer"]["teams"]["nodes"]

            if not teams:
                raise Exception("No teams found. Please create a team in Linear first.")

            team = teams[0]
            self.workspace_id = team["organization"]["id"]
            self.team_id = team["id"]

            print(f"✅ Connected to Linear")
            print(f"   Workspace: {self.workspace_id}")
            print(f"   Team: {self.team_id}")

            return self.workspace_id, self.team_id
        except Exception as e:
            print(f"❌ Failed to authenticate: {e}")
            print("Make sure LINEAR_API_TOKEN is valid")
            raise


def load_yaml(filepath: str) -> Dict:
    """Load YAML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        raise


def main():
    print("🚀 Starting Linear Task Publisher")
    print("=" * 60)

    # Check API token
    api_token = os.getenv("LINEAR_API_TOKEN")
    if not api_token:
        print("❌ ERROR: LINEAR_API_TOKEN environment variable not set")
        sys.exit(1)

    print(f"✅ LINEAR_API_TOKEN found ({api_token[:20]}...)")

    # Find config files
    print("\n📂 Looking for config files...")
    task_path, linear_path = get_config_paths()

    if not task_path or not linear_path:
        print("❌ Config files not found")
        sys.exit(1)

    print(f"✅ task-package.yaml: {task_path}")
    print(f"✅ linear-publish.yaml: {linear_path}")

    # Load configurations
    print("\n📥 Loading configurations...")
    try:
        task_package = load_yaml(task_path)
        linear_config = load_yaml(linear_path)
        print(f"✅ Loaded {len(task_package.get('tasks', []))} tasks")
    except Exception as e:
        print(f"❌ Failed to load configs: {e}")
        sys.exit(1)

    # Connect to Linear
    print("\n🔗 Connecting to Linear...")
    client = LinearClient(api_token)

    try:
        client.get_workspace_and_team()
    except Exception as e:
        print(f"❌ Linear connection failed: {e}")
        sys.exit(1)

    # Prepare results
    results = {
        "workspace_id": client.workspace_id,
        "team_id": client.team_id,
        "timestamp": datetime.now().isoformat(),
        "issues_created": 0,
        "tasks_total": len(task_package.get('tasks', [])),
        "issues": [],
        "errors": []
    }

    print("\n" + "=" * 60)
    print("📋 TASKS LOADED - READY FOR PUBLICATION")
    print("=" * 60)
    print(f"Tasks to publish: {results['tasks_total']}")
    print(f"Workspace: {results['workspace_id']}")
    print(f"Team: {results['team_id']}")

    print("\n⚠️  NOTE: Full publication requires Linear API implementation")
    print("For now, showing what would be published:")
    print()

    # List tasks that would be created
    for task in task_package.get('tasks', []):
        task_id = task.get('id')
        task_config = linear_config.get('mapping', {}).get(task_id, {})

        if task_config:
            title = task_config.get('title', task.get('title'))
            print(f"  ✓ {task_id}: {title[:60]}")
            results['issues'].append({
                "task_id": task_id,
                "title": title,
                "status": "ready_to_publish"
            })
        else:
            results['errors'].append(f"No Linear config for {task_id}")

    results['issues_created'] = len(results['issues'])

    # Save results
    print("\n💾 Saving results...")
    output_dir = os.path.dirname(task_path)
    output_path = os.path.join(output_dir, "linear-publish-results.json")

    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✅ Results saved: {output_path}")
    except Exception as e:
        print(f"❌ Failed to save results: {e}")
        sys.exit(1)

    # Summary
    print("\n" + "=" * 60)
    print(f"✅ SUCCESS: {results['issues_created']}/{results['tasks_total']} tasks ready")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"1. Review the issues listed above")
    print(f"2. Full Linear API integration coming in next update")
    print(f"3. Results saved to: {output_path}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

import pandas as pd
import re
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fedrisk_api.db.models import Task, TaskChild, WorkflowFlowchart
import uuid


def scan_spreadsheet(file_path):
    df = pd.read_excel(file_path)
    suspicious_cells = []

    patterns = [
        r"=cmd",
        r"=powershell",
        r"=WEBSERVICE",
        r"=EXEC",
        r"=SHELL",
        r"<script>",
        r"javascript:",
        r"onerror=",
        r"onload=",
    ]

    for index, row in df.iterrows():
        for col_name, value in row.items():
            if isinstance(value, str):
                for pattern in patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        suspicious_cells.append(
                            {
                                "row_index": index,
                                "column": col_name,
                                "value": value,
                                "pattern": pattern,
                            }
                        )
                        break
    return suspicious_cells


def safe_import_spreadsheet(file_path):
    suspicious = scan_spreadsheet(file_path)
    if suspicious:
        print("🚨 Import blocked due to suspicious content found in the spreadsheet:")
        for cell in suspicious:
            print(
                f"Row {cell['row_index']} - Column '{cell['column']}': {cell['value']} (matched: {cell['pattern']})"
            )
        return False

    print("✅ No suspicious content found. Proceeding with import...")
    return True


def import_workflow_flowchart_from_excel(
    file_path: str, db: Session, user_id: int, tenant_id: int, project_id: int
):
    df = pd.read_excel(file_path)
    print("Excel columns:", list(df.columns))
    now = datetime.utcnow()
    workflows = []

    if df.empty:
        print("\u26a0\ufe0f No data found in Excel sheet.")
        return workflows

    grouped = df.groupby("Workflow Name")

    for workflow_base_name, group in grouped:
        task_map = {}
        parent_relations = {}
        conditional_nodes = {}
        existing_links = set()

        node_data = []
        link_data = []

        workflow_name = f"Import {workflow_base_name.strip()} {now.strftime('%Y-%m-%d %H:%M')}"

        start_key = "start"
        end_key = "end"

        node_data.append(
            {"key": start_key, "category": "Start", "text": "Start", "loc": "-100 -100"}
        )
        node_data.append({"key": end_key, "category": "End", "text": "End", "loc": "0 0"})

        new_flowchart = WorkflowFlowchart(
            name=workflow_name,
            node_data=[],
            link_data=[],
            project_id=project_id,
            start_date=now,
            due_date=now + timedelta(days=30),
            status="not_started",
        )
        db.add(new_flowchart)
        db.commit()
        db.refresh(new_flowchart)

        # Step 1: Create tasks and track relationships
        for _, row in group.iterrows():
            task_name = str(row["Task Name"]).strip()
            task_name_trimmed = task_name[:30]
            start_date = pd.to_datetime(row.get("Start Date"), errors="coerce")
            due_date = pd.to_datetime(row.get("Due Date"), errors="coerce")
            trimmed_description = str(row["Task Description"]).strip()[:199]

            task = Task(
                title=task_name_trimmed,
                name=task_name,
                description=trimmed_description,
                actual_start_date=start_date.to_pydatetime() if not pd.isna(start_date) else None,
                due_date=due_date.to_pydatetime() if not pd.isna(due_date) else None,
                user_id=user_id,
                tenant_id=tenant_id,
                project_id=project_id,
            )
            db.add(task)
            db.flush()

            task_map[task_name] = task

            # Record parent
            parent_name = row.get("Parent Task")
            if pd.notna(parent_name):
                parent_relations.setdefault(task_name, set()).add(str(parent_name).strip())

            # Record conditional
            conditions = row.get("Conditions")
            if pd.notna(conditions):
                conditional_key = str(uuid.uuid4())
                conditional_nodes[task_name] = {
                    "key": conditional_key,
                    "category": "Conditional",
                    "text": conditions,
                    "loc": "0 0",  # placeholder
                    "completed": False,
                }

        db.commit()

        # Step 2: Tree layout using DFS, horizontal parents, vertical children
        from collections import defaultdict

        graph = defaultdict(set)
        inverse_graph = defaultdict(set)
        for child, parents in parent_relations.items():
            for parent in parents:
                graph[parent].add(child)
                inverse_graph[child].add(parent)

        roots = list(set(task_map) - set(inverse_graph))
        placed = set()
        node_positions = {}
        x_step, y_step = 200, 150

        def layout_tree(task_name, x, y):
            task_id = str(task_map[task_name].id)
            node_positions[task_id] = (x, y)
            placed.add(task_name)
            children = sorted(graph.get(task_name, []))
            for i, child in enumerate(children):
                if child not in placed:
                    layout_tree(child, x, y + i + 1)

        for i, root in enumerate(sorted(roots)):
            layout_tree(root, i, 0)

        # Fallback for unlinked tasks
        unplaced_tasks = [t for t in task_map if t not in placed]
        if unplaced_tasks:
            fallback_x = len(roots)
            fallback_y = max((y for _, y in node_positions.values()), default=-1) + 1
            for i, task_name in enumerate(unplaced_tasks):
                layout_tree(task_name, fallback_x, fallback_y + i)

        # Step 3: Build node_data and apply positions
        for task_name, task in task_map.items():
            task_id = str(task.id)
            x, y = node_positions[task_id]
            node_data.append(
                {
                    "key": task_id,
                    "category": "Unlinked",
                    "text": task.name,
                    "loc": f"{x * x_step} {y * y_step}",
                }
            )

            # Conditional nodes (to the left)
            if task_name in conditional_nodes:
                cond = conditional_nodes[task_name]
                cond["loc"] = f"{(x - 1) * x_step} {y * y_step}"
                node_data.append(cond)
                link_data.append(
                    {
                        "from": cond["key"],
                        "to": task_id,
                        "key": str(uuid.uuid4()),
                    }
                )

        # Step 4: Link parents and children
        all_parents, all_children = set(), set()
        for child_name, parents in parent_relations.items():
            child_task = task_map.get(child_name)
            for parent_name in parents:
                parent_task = task_map.get(parent_name)
                if not parent_task or not child_task:
                    continue
                db.add(TaskChild(parent_task_id=parent_task.id, child_task_id=child_task.id))
                link_data.append(
                    {
                        "from": str(parent_task.id),
                        "to": str(child_task.id),
                        "key": str(uuid.uuid4()),
                    }
                )
                all_parents.add(str(parent_task.id))
                all_children.add(str(child_task.id))

        # Step 5: Categorize nodes
        for node in node_data:
            key = str(node["key"])
            if node["category"] in ("Start", "End", "Conditional"):
                continue
            if key in all_parents:
                node["category"] = "Parent"
            elif key in all_children:
                node["category"] = "Child"
            else:
                node["category"] = "Child"

        # Step 6: Add Start/End links
        parent_nodes = [n for n in node_data if n["category"] == "Parent"]
        if parent_nodes:
            first_key = parent_nodes[0]["key"]
            last_key = parent_nodes[-1]["key"]
            link_data.append({"from": start_key, "to": first_key, "key": str(uuid.uuid4())})
            link_data.append({"from": last_key, "to": end_key, "key": str(uuid.uuid4())})

        new_flowchart.node_data = node_data
        new_flowchart.link_data = link_data
        db.commit()

        workflows.append(new_flowchart)
        print(
            f"\u2705 Imported workflow '{workflow_base_name}' with {len(node_data)} nodes and {len(link_data)} links."
        )

    print(f"Imported {len(workflows)} workflows.")
    return workflows

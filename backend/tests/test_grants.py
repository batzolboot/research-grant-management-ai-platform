from datetime import date, timedelta


def test_create_grant(client):
    response = client.post(
        "/grants",
        json={
            "title": "Test Research Grant",
            "principal_investigator": "Dr. Test",
            "funding_agency": "Test Agency",
            "amount": 50000,
            "deadline": "2026-12-15",
            "status": "Pending",
            "compliance_status": "Complete",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["title"] == "Test Research Grant"
    assert data["principal_investigator"] == "Dr. Test"
    assert data["amount"] == "50000.00"
    assert data["status"] == "Pending"


def test_get_grants(client):
    client.post(
        "/grants",
        json={
            "title": "Grant One",
            "principal_investigator": "Dr. One",
            "funding_agency": "Agency One",
            "amount": 10000,
            "deadline": "2026-12-15",
            "status": "Active",
            "compliance_status": "Complete",
        },
    )

    response = client.get("/grants")

    assert response.status_code == 200

    grants = response.json()

    assert len(grants) == 1
    assert grants[0]["title"] == "Grant One"


def test_deadline_within_thirty_days_becomes_urgent(client):
    deadline = date.today() + timedelta(days=15)

    response = client.post(
        "/grants",
        json={
            "title": "Urgent Grant",
            "principal_investigator": "Dr. Urgent",
            "funding_agency": "Urgent Agency",
            "amount": 75000,
            "deadline": deadline.isoformat(),
            "status": "Pending",
            "compliance_status": "Complete",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "Urgent"


def test_missing_compliance_creates_task(client):
    response = client.post(
        "/grants",
        json={
            "title": "Compliance Test",
            "principal_investigator": "Dr. Compliance",
            "funding_agency": "Test Agency",
            "amount": 25000,
            "deadline": "2026-12-15",
            "status": "Pending",
            "compliance_status": None,
        },
    )

    assert response.status_code == 201

    tasks_response = client.get("/tasks")

    assert tasks_response.status_code == 200

    tasks = tasks_response.json()

    assert len(tasks) == 1
    assert tasks[0]["grant_id"] == response.json()["id"]
    assert tasks[0]["title"] == "Review missing compliance"
    assert tasks[0]["priority"] == "High"
    assert tasks[0]["status"] == "Open"


def test_grant_creation_creates_audit_log(client):
    response = client.post(
        "/grants",
        json={
            "title": "Audit Test Grant",
            "principal_investigator": "Dr. Audit",
            "funding_agency": "Audit Agency",
            "amount": 30000,
            "deadline": "2026-12-15",
            "status": "Pending",
            "compliance_status": "Complete",
        },
    )

    assert response.status_code == 201

    logs_response = client.get("/audit-logs")

    assert logs_response.status_code == 200

    logs = logs_response.json()

    assert len(logs) == 1
    assert logs[0]["action"] == "CREATE"
    assert logs[0]["resource_type"] == "Grant"
    assert logs[0]["resource_id"] == response.json()["id"]

def create_test_grant(client, compliance_status="Complete"):
    response = client.post(
        "/grants",
        json={
            "title": "Reusable Test Grant",
            "principal_investigator": "Dr. Reusable",
            "funding_agency": "Reusable Agency",
            "amount": 40000,
            "deadline": "2026-12-15",
            "status": "Pending",
            "compliance_status": compliance_status,
        },
    )

    assert response.status_code == 201

    return response.json()


def test_update_grant(client):
    grant = create_test_grant(client)

    response = client.put(
        f"/grants/{grant['id']}",
        json={
            "title": "Updated Test Grant",
            "amount": 55000,
            "status": "Active",
        },
    )

    assert response.status_code == 200

    updated_grant = response.json()

    assert updated_grant["id"] == grant["id"]
    assert updated_grant["title"] == "Updated Test Grant"
    assert updated_grant["amount"] == "55000.00"
    assert updated_grant["status"] == "Active"


def test_update_nonexistent_grant_returns_404(client):
    response = client.put(
        "/grants/9999",
        json={
            "title": "Does Not Exist",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Grant not found"


def test_delete_grant(client):
    grant = create_test_grant(client)

    delete_response = client.delete(
        f"/grants/{grant['id']}"
    )

    assert delete_response.status_code == 200
    assert (
        delete_response.json()["message"]
        == "Grant deleted successfully"
    )

    get_response = client.get(
        f"/grants/{grant['id']}"
    )

    assert get_response.status_code == 404


def test_delete_grant_creates_audit_log(client):
    grant = create_test_grant(client)

    response = client.delete(
        f"/grants/{grant['id']}"
    )

    assert response.status_code == 200

    logs_response = client.get("/audit-logs")

    assert logs_response.status_code == 200

    logs = logs_response.json()

    delete_logs = [
        log
        for log in logs
        if log["action"] == "DELETE"
    ]

    assert len(delete_logs) == 1
    assert delete_logs[0]["resource_id"] == grant["id"]
    assert (
        delete_logs[0]["details"]
        == "Deleted grant: Reusable Test Grant"
    )


def test_complete_task(client):
    grant = create_test_grant(
        client,
        compliance_status=None,
    )

    tasks_response = client.get("/tasks")

    assert tasks_response.status_code == 200

    tasks = tasks_response.json()

    assert len(tasks) == 1

    task_id = tasks[0]["id"]

    update_response = client.put(
        f"/tasks/{task_id}",
        json={
            "status": "Completed",
        },
    )

    assert update_response.status_code == 200

    completed_task = update_response.json()

    assert completed_task["status"] == "Completed"
    assert completed_task["completed_at"] is not None
    assert completed_task["grant_id"] == grant["id"]


def test_reopen_task(client):
    create_test_grant(
        client,
        compliance_status=None,
    )

    tasks = client.get("/tasks").json()
    task_id = tasks[0]["id"]

    client.put(
        f"/tasks/{task_id}",
        json={
            "status": "Completed",
        },
    )

    reopen_response = client.put(
        f"/tasks/{task_id}",
        json={
            "status": "Open",
        },
    )

    assert reopen_response.status_code == 200

    reopened_task = reopen_response.json()

    assert reopened_task["status"] == "Open"
    assert reopened_task["completed_at"] is None


def test_invalid_task_status_is_rejected(client):
    create_test_grant(
        client,
        compliance_status=None,
    )

    tasks = client.get("/tasks").json()
    task_id = tasks[0]["id"]

    response = client.put(
        f"/tasks/{task_id}",
        json={
            "status": "NotARealStatus",
        },
    )

    assert response.status_code == 422


def test_csv_report_export(client):
    create_test_grant(client)

    response = client.get("/reports/grants.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/csv"
    )
    assert (
        "attachment; filename=\"grant_report.csv\""
        in response.headers["content-disposition"]
    )

    csv_text = response.text

    assert "Reusable Test Grant" in csv_text
    assert "Dr. Reusable" in csv_text
    assert "Reusable Agency" in csv_text


def test_excel_report_export(client):
    create_test_grant(client)

    response = client.get("/reports/grants.xlsx")

    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    )
    assert (
        "attachment; filename=\"grant_report.xlsx\""
        in response.headers["content-disposition"]
    )

    assert len(response.content) > 0
    assert response.content[:2] == b"PK"
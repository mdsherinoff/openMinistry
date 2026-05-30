"""
End-to-end moderation workflow tests.
Usage: python moderation/test_workflow.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.WARNING)

import httpx
import json

BASE_URL = "http://localhost:8000"


class ModerationWorkflowTester:
    def __init__(self):
        self.token = None
        self.mod_token = None
        self.client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    def get_token(self, email: str, password: str) -> str:
        res = self.client.post("/api/auth/login", json={
            "email": email,
            "password": password,
        })
        assert res.status_code == 200, f"Login failed: {res.text}"
        return res.json()["access_token"]

    def auth_headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    # -------------------------
    # Test 1 — Authentication
    # -------------------------
    def test_auth(self):
        print("Test 1: Authentication & permissions")

        # Admin login
        self.token = self.get_token(
            "admin@openministry.in", "admin123"
        )
        print("Admin login works")

        # Moderator login
        self.mod_token = self.get_token(
            "moderator@openministry.in", "mod123"
        )
        print("Moderator login works")

        # Wrong password
        res = self.client.post("/api/auth/login", json={
            "email": "admin@openministry.in",
            "password": "wrongpassword",
        })
        assert res.status_code == 401
        print("Wrong password correctly rejected")

        # Unauthenticated queue access
        res = self.client.get("/api/moderation/queue")
        assert res.status_code == 401
        print("Unauthenticated queue access correctly rejected")

        # Public statements endpoint works without auth
        res = self.client.get("/api/statements/")
        assert res.status_code == 200
        print("Public statements endpoint accessible")

    # -------------------------
    # Test 2 — Queue Access
    # -------------------------
    def test_queue(self):
        print("\nTest 2: Queue access and filtering")

        headers = self.auth_headers(self.token)

        # Get queue
        res = self.client.get(
            "/api/moderation/queue",
            headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "statements" in data
        total = data["total"]
        print(f"Queue accessible — {total} pending statements")

        # Filter by confidence
        res = self.client.get(
            "/api/moderation/queue?min_confidence=0.8",
            headers=headers
        )
        assert res.status_code == 200
        high_conf = res.json()["total"]
        print(f"Confidence filter works — {high_conf} high confidence")

        # Pagination
        res = self.client.get(
            "/api/moderation/queue?limit=5&offset=0",
            headers=headers
        )
        assert res.status_code == 200
        assert len(res.json()["statements"]) <= 5
        print("Pagination works")

        return data["statements"][0]["id"] if data["statements"] else None

    # -------------------------
    # Test 3 — Approve Flow
    # -------------------------
    def test_approve(self, statement_id: int):
        print("\nTest 3: Approve workflow")
        headers = self.auth_headers(self.token)

        # Get statement context
        res = self.client.get(
            f"/api/moderation/{statement_id}/context",
            headers=headers
        )
        assert res.status_code == 200
        context = res.json()
        assert "minister_name" in context
        assert "article_url" in context
        print(f"Context loaded for statement {statement_id}")
        print(f"Minister: {context['minister_name']}")

        # Approve it
        res = self.client.post(
            f"/api/moderation/{statement_id}/approve",
            headers=headers,
            params={"notes": "test approval"},
        )
        assert res.status_code == 200
        print(f"Statement {statement_id} approved")

        # Verify status changed
        res = self.client.get(
            f"/api/statements/{statement_id}",
        )
        assert res.status_code == 200
        assert res.json()["status"] == "approved"
        print("Status correctly updated to approved")

        # Verify audit log created
        res = self.client.get(
            f"/api/moderation/{statement_id}/logs",
            headers=headers
        )
        assert res.status_code == 200
        logs = res.json()
        assert len(logs) > 0
        assert logs[0]["action"] == "approved"
        print("Audit log created correctly")

        return statement_id

    # -------------------------
    # Test 4 — Reject Flow
    # -------------------------
    def test_reject(self, statement_id: int):
        print("\nTest 4: Reject workflow")
        headers = self.auth_headers(self.token)

        res = self.client.post(
            f"/api/moderation/{statement_id}/reject",
            headers=headers,
            params={"notes": "test rejection — misattributed"},
        )
        assert res.status_code == 200
        print(f"Statement {statement_id} rejected")

        # Verify status
        res = self.client.get(f"/api/statements/{statement_id}")
        assert res.status_code == 200
        assert res.json()["status"] == "rejected"
        print("Status correctly updated to rejected")

        # Verify audit log
        res = self.client.get(
            f"/api/moderation/{statement_id}/logs",
            headers=headers
        )
        logs = res.json()
        assert any(log["action"] == "rejected" for log in logs)
        print("Rejection audit log created")

    # -------------------------
    # Test 5 — Edit Flow
    # -------------------------
    def test_edit(self, statement_id: int):
        print("\nTest 5: Edit workflow")
        headers = self.auth_headers(self.token)

        edited_text = (
            "The minister announced that the government would "
            "strengthen public hospitals across the state."
        )

        res = self.client.post(
            f"/api/moderation/{statement_id}/review",
            headers=headers,
            json={
                "action": "edited",
                "edited_text": edited_text,
                "notes": "fixed extraction error",
            }
        )
        assert res.status_code == 200
        print(f"Statement {statement_id} edited")

        # Verify text was updated
        res = self.client.get(f"/api/statements/{statement_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["statement_text"] == edited_text
        assert data["status"] == "approved"
        print("Text updated and auto-approved")

        # Verify audit log has previous text
        res = self.client.get(
            f"/api/moderation/{statement_id}/logs",
            headers=headers
        )
        logs = res.json()
        edit_log = next(
            (l for l in logs if l["action"] == "edited"), None
        )
        assert edit_log is not None
        assert edit_log["previous_text"] is not None
        print("Previous text preserved in audit log")

    # -------------------------
    # Test 6 — Moderator Permissions
    # -------------------------
    def test_permissions(self, statement_id: int):
        print("\nTest 6: Role permissions")
        mod_headers = self.auth_headers(self.mod_token)
        admin_headers = self.auth_headers(self.token)

        # Moderator CAN access queue
        res = self.client.get(
            "/api/moderation/queue",
            headers=mod_headers
        )
        assert res.status_code == 200
        print("Moderator can access queue")

        # Moderator CAN approve
        res = self.client.post(
            f"/api/moderation/{statement_id}/approve",
            headers=mod_headers,
        )
        assert res.status_code == 200
        print("Moderator can approve statements")

        # Moderator CANNOT create sources (admin only)
        res = self.client.post(
            "/api/sources/",
            headers=mod_headers,
            json={
                "name": "Test Source",
                "website": "https://test.com",
                "language": "en",
            }
        )
        assert res.status_code == 403
        print("Moderator correctly blocked from admin-only endpoints")

        # Admin CAN create sources
        res = self.client.post(
            "/api/sources/",
            headers=admin_headers,
            json={
                "name": "Test Source Delete Me",
                "website": "https://testdeleteme123.com",
                "language": "en",
            }
        )
        assert res.status_code == 200
        source_id = res.json()["id"]
        print("Admin can create sources")

        # Clean up
        self.client.delete(
            f"/api/sources/{source_id}",
            headers=admin_headers
        )

    # -------------------------
    # Test 7 — Stats
    # -------------------------
    def test_stats(self):
        print("\nTest 7: Statistics")
        headers = self.auth_headers(self.token)

        res = self.client.get(
            "/api/moderation/stats/overview",
            headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert "totals" in data
        assert data["totals"]["approved"] > 0
        print(f"Stats endpoint works")
        print(f"Approved: {data['totals']['approved']}")
        print(f"Pending: {data['totals']['pending']}")
        print(f"Rejected: {data['totals']['rejected']}")

        # Public stats endpoint
        res = self.client.get("/api/statements/stats")
        assert res.status_code == 200
        print("Public stats endpoint works")

    # -------------------------
    # Test 8 — Edge Cases
    # -------------------------
    def test_edge_cases(self):
        print("\nTest 8: Edge cases")
        headers = self.auth_headers(self.token)

        # Non-existent statement
        res = self.client.post(
            "/api/moderation/999999/approve",
            headers=headers,
        )
        assert res.status_code == 404
        print("Non-existent statement returns 404")

        # Invalid action
        res = self.client.post(
            "/api/moderation/1/review",
            headers=headers,
            json={"action": "invalid_action"},
        )
        assert res.status_code == 400
        print("Invalid action correctly rejected")

        # Edit with empty text
        res = self.client.post(
            "/api/moderation/1/review",
            headers=headers,
            json={
                "action": "edited",
                "edited_text": "short",
            }
        )
        assert res.status_code == 400
        print("Too-short edit text correctly rejected")

    def run_all(self):
        print("Running Moderation Workflow Tests\n")
        print("=" * 50)

        try:
            self.test_auth()
            statement_id = self.test_queue()

            if not statement_id:
                print("\nNo pending statements found.")
                print("Run the pipeline first:")
                print("  python nlp/test_extraction.py")
                return

            # Use different statements for each test
            self.test_approve(statement_id)

            # Get another pending statement for reject test
            headers = self.auth_headers(self.token)
            res = self.client.get(
                "/api/moderation/queue?limit=3",
                headers=headers
            )
            statements = res.json().get("statements", [])

            if len(statements) >= 1:
                self.test_reject(statements[0]["id"])
            if len(statements) >= 2:
                self.test_edit(statements[1]["id"])

            self.test_permissions(statement_id)
            self.test_stats()
            self.test_edge_cases()

            print("\n" + "=" * 50)
            print("All tests passed!")

        except AssertionError as e:
            print(f"\nTest failed: {e}")
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            raise
        finally:
            self.client.close()


if __name__ == "__main__":
    tester = ModerationWorkflowTester()
    tester.run_all()
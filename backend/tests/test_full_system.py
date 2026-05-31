"""
Full system end-to-end tests.
Run: python tests/test_full_system.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import httpx
import json

BASE_URL = "http://localhost:8000"


class SystemTester:
    def __init__(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=30.0)
        self.token = None
        self.passed = 0
        self.failed = 0

    def check(self, name: str, condition: bool, detail: str = ""):
        if condition:
            print(f"{name}")
            self.passed += 1
        else:
            print(f"{name} {detail}")
            self.failed += 1

    def get_token(self):
        res = self.client.post("/api/auth/login", json={
            "email": "admin@openministry.in",
            "password": "admin123",
        })
        self.token = res.json().get("access_token")
        return self.token

    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    # ─────────────────────────────
    # Test 1 — Infrastructure
    # ─────────────────────────────
    def test_infrastructure(self):
        print("\nInfrastructure")

        res = self.client.get("/health")
        data = res.json()
        self.check("Health endpoint responds", res.status_code == 200)
        self.check(
            "Database connected",
            data.get("checks", {}).get("database") == "connected"
        )
        self.check(
            "Redis connected",
            data.get("checks", {}).get("redis") == "connected"
        )

        res = self.client.get("/")
        self.check("Root endpoint responds", res.status_code == 200)
        self.check(
            "API links in root",
            "statements" in res.json().get("api", {})
        )

    # ─────────────────────────────
    # Test 2 — Authentication
    # ─────────────────────────────
    def test_authentication(self):
        print("\nAuthentication")

        token = self.get_token()
        self.check("Admin login works", bool(token))

        res = self.client.get("/api/moderation/queue")
        self.check(
            "Unauthenticated request rejected",
            res.status_code == 401
        )

        res = self.client.get(
            "/api/moderation/queue",
            headers=self.auth_headers()
        )
        self.check(
            "Authenticated request works",
            res.status_code == 200
        )

        res = self.client.post("/api/auth/login", json={
            "email": "admin@openministry.in",
            "password": "wrongpassword",
        })
        self.check(
            "Wrong password rejected",
            res.status_code == 401
        )

    # ─────────────────────────────
    # Test 3 — Public API
    # ─────────────────────────────
    def test_public_api(self):
        print("\nPublic API")

        # Statements
        res = self.client.get("/api/v1/statements")
        self.check("GET /api/v1/statements", res.status_code == 200)
        data = res.json()
        self.check(
            "Statements returns results",
            data.get("total", 0) > 0,
            f"(total={data.get('total', 0)})"
        )

        # Pagination
        res = self.client.get("/api/v1/statements?limit=5&offset=0")
        self.check(
            "Pagination works",
            len(res.json().get("results", [])) <= 5
        )

        # Ministers
        res = self.client.get("/api/v1/ministers")
        self.check("GET /api/v1/ministers", res.status_code == 200)
        self.check(
            "Ministers returns results",
            res.json().get("total", 0) > 0
        )

        # Search
        res = self.client.get("/api/v1/search?q=minister")
        self.check("GET /api/v1/search", res.status_code == 200)

        # Topics
        res = self.client.get("/api/v1/topics")
        self.check("GET /api/v1/topics", res.status_code == 200)

        # Single statement
        statements = self.client.get(
            "/api/v1/statements?limit=1"
        ).json().get("results", [])
        if statements:
            stmt_id = statements[0]["id"]
            res = self.client.get(f"/api/v1/statements/{stmt_id}")
            self.check(
                "GET /api/v1/statements/{id}",
                res.status_code == 200
            )
            data = res.json()
            self.check(
                "Statement has required fields",
                all(k in data for k in [
                    "id", "text", "minister", "source"
                ])
            )

        # 404 handling
        res = self.client.get("/api/v1/statements/999999")
        self.check("Non-existent statement returns 404", res.status_code == 404)

    # ─────────────────────────────
    # Test 4 — Scraping Pipeline
    # ─────────────────────────────
    def test_pipeline(self):
        print("\nScraping Pipeline")

        from database.config import get_session_factory
        from database.models.article import Article
        from database.models.statement import Statement
        from database.models.minister import Minister

        db = get_session_factory()()

        article_count = db.query(Article).count()
        self.check(
            f"Articles in database ({article_count})",
            article_count > 0
        )

        statement_count = db.query(Statement).count()
        self.check(
            f"Statements in database ({statement_count})",
            statement_count > 0
        )

        approved = db.query(Statement).filter(
            Statement.status == "approved"
        ).count()
        self.check(
            f"Approved statements ({approved})",
            approved > 0
        )

        minister_count = db.query(Minister).filter(
            Minister.is_active == 1
        ).count()
        self.check(
            f"Ministers in database ({minister_count})",
            minister_count > 100
        )

        tagged = db.query(Statement).filter(
            Statement.topic.isnot(None),
            Statement.status == "approved",
        ).count()
        self.check(
            f"Tagged statements ({tagged})",
            tagged > 0
        )

        db.close()

    # ─────────────────────────────
    # Test 5 — Moderation
    # ─────────────────────────────
    def test_moderation(self):
        print("\nModeration")

        headers = self.auth_headers()

        res = self.client.get(
            "/api/moderation/queue",
            headers=headers
        )
        self.check("Queue accessible", res.status_code == 200)
        data = res.json()
        self.check(
            "Queue returns statements",
            "statements" in data and "total" in data
        )

        res = self.client.get(
            "/api/moderation/stats/overview",
            headers=headers
        )
        self.check("Stats endpoint works", res.status_code == 200)
        stats = res.json()
        self.check(
            "Stats has required fields",
            "totals" in stats and "approved" in stats["totals"]
        )

    # ─────────────────────────────
    # Test 6 — Search
    # ─────────────────────────────
    def test_search(self):
        print("\nSearch")

        # Basic search
        res = self.client.get("/api/search/?q=minister")
        self.check("Basic search works", res.status_code == 200)

        # Minister search
        res = self.client.get("/api/search/ministers?q=Satheesan")
        self.check("Minister search works", res.status_code == 200)
        results = res.json()
        self.check(
            "Minister search finds Satheesan",
            len(results) > 0
        )

        # Suggestions
        res = self.client.get("/api/search/suggestions?q=health")
        self.check("Suggestions endpoint works", res.status_code == 200)

        # Empty query rejected
        res = self.client.get("/api/search/?q=a")
        self.check(
            "Too-short query rejected",
            res.status_code == 422
        )

    # ─────────────────────────────
    # Test 7 — Security
    # ─────────────────────────────
    def test_security(self):
        print("\nSecurity")

        res = self.client.get("/api/v1/statements")
        headers = dict(res.headers)

        self.check(
            "X-Content-Type-Options header present",
            "x-content-type-options" in headers
        )
        self.check(
            "X-Frame-Options header present",
            "x-frame-options" in headers
        )
        self.check(
            "Request ID header present",
            "x-request-id" in headers
        )

        # SQL injection attempt
        res = self.client.get(
            "/api/v1/search?q='; DROP TABLE statements; --"
        )
        self.check(
            "SQL injection handled gracefully",
            res.status_code in (200, 422)
        )

        # Admin endpoints require auth
        for endpoint in [
            "/api/moderation/queue",
            "/api/moderation/stats/overview",
            "/api/sources/",
        ]:
            res = self.client.get(endpoint)
            self.check(
                f"Auth required for {endpoint}",
                res.status_code == 401
            )

    # ─────────────────────────────
    # Run All Tests
    # ─────────────────────────────
    def run_all(self):
        print("openMinistry Full System Tests")
        print("=" * 50)

        try:
            self.test_infrastructure()
            self.test_authentication()
            self.test_public_api()
            self.test_pipeline()
            self.test_moderation()
            self.test_search()
            self.test_security()
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.client.close()

        print("\n" + "=" * 50)
        print(f"Results: {self.passed} passed, {self.failed} failed")

        if self.failed == 0:
            print("All tests passed — ready for launch!")
        else:
            print(f"{self.failed} test(s) need attention")


if __name__ == "__main__":
    tester = SystemTester()
    tester.run_all()
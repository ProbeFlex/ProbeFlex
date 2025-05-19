<p align="center">
  <img src="ProbeFlex.png" alt="ProbeFlex Logo" width="220"/>
</p>

---

## What is ProbeFlex?

**ProbeFlex** is a comprehensive open-source toolkit—built with **Python 3.13 + Django 5.2 + Django REST Framework**—for designing, running, and monitoring API tests at any scale.  
Think of it as an *"API test laboratory meets CI integration"*:

- **Test API endpoints in real-time** and view structured responses  
- **Record & replay** interactive sessions as repeatable test scenarios  
- **Schedule** smoke / regression tests or run load tests via Celery workers  
- **Visual dashboards** tracking uptime, latency, error trends, and SLA compliance  
- **Extensible plugin system** (assertion DSL, authentication flows, custom reporters)  

> Whether you need a quick local testing environment or a production-grade monitoring system, ProbeFlex's flexible architecture adapts to your needs.

---

## Quick Start

```bash
# 1 Clone
git clone https://github.com/ProbeFlex/ProbeFlex.git
cd ProbeFlex

# 2 Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 3 Install dependencies
pip install -r requirements/dev.txt  # includes Django, DRF, Celery, etc.

# 4 Configure .env file
cp .env.example .env              # set up DB, Redis and secret key

# 5 Run migrations and load demo data
python manage.py migrate
python manage.py loaddata demo

# 6 Run the application
python manage.py runserver
celery -A probeflex worker -l info     # async job runner
```

Open **`http://127.0.0.1:8000/`** → log in with `demo / demo123` to explore the UI.

---

## Core Features

| Module            | Highlights                                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------------ |
| **Live Testing**  | Curl-like request builder, environment variables, authentication helpers (Bearer, OAuth2, HMAC).  |
| **Test Suite**    | YAML / UI writer, rich validations (`status_code`, JSONPath, regex, latency), parameterized runs. |
| **Scheduler**     | Cron-style or push triggers (GitHub/GitLab CI).                                                  |
| **Load Lab**      | k6-compatible scripts, distributed Celery queue, Grafana exporter.                               |
| **Observability** | Prometheus metrics, OpenTelemetry traces, Slack / Discord alerts.                                |
| **Integrations**  | Postman collection import, pytest plugin, GitHub Checks annotations.                              |

---

## Architecture

```
             ┌────────────┐
             │  Frontend  │  (Next.js UI, Tailwind, SWR)
             └─────┬──────┘
                   │ REST / WebSocket
┌──────────────────┼───────────────────────────────────────────────┐
│              Django API Server                                   │
│  ┌─────────────┴─────────────┐          ┌──────────────────────┐ │
│  │ Request/Test Engine       │  Celery  │ Async Worker Pool    │ │
│  │  • parser / validator     │ <──────> │  • run steps         │ │
│  │  • assertion DSL          │          │  • notify hooks      │ │
│  └─────────────┬─────────────┘          └────────────┬─────────┘ │
│        PostgreSQL                     Redis (broker/TTL metrics) │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

* **Backend:** Django 5, Django REST Framework, Celery, Redis
* **Database:** PostgreSQL 15
* **Task Runner:** Celery + RabbitMQ/Redis (default Redis)
* **CI/CD:** GitHub Actions + Docker Compose
* **Observability:** Prometheus, Grafana, Sentry (optional)
* **Packaging:** Poetry + PEP 517 wheel; PyPI: `probeflex`

---

## 🗺️ Roadmap

* [ ] GraphQL sandbox and tests
* [ ] gRPC testing + protobuf validation helpers
* [ ] AI-powered test suggestions (OpenAI function-calling)
* [ ] Multi-tenant SaaS mode
* [ ] k6 cloud export

---

## 🤝 Contributing

We 💚 PRs!

1. Fork and create a branch from `main`
2. `poetry install` / `pre-commit install`
3. Add tests (`pytest`) and run `make check`
4. Submit PR - CI will run lint, unit and integration tests

Check **CONTRIBUTING.md** for coding guidelines and commit conventions (Conventional Commits).

---

## 📜 License

ProbeFlex is released under the **MIT License** - see `LICENSE` file.

---

## 🌍 Community & Support

* **Discussions:** [https://github.com/ProbeFlex/ProbeFlex/discussions](https://github.com/ProbeFlex/ProbeFlex/discussions)

---

> **Test, probe, flex.**
> May your APIs always return **200 OK**.

---

## Donation and Support 
If you appreciate our work and wish to support the continuation and expansion of our project, please consider making a donation. Your contributions will enable us to keep improving and add new features. You can donate to the following cryptocurrency addresses. Thank you for your support!

* **USDT**: 0xa5a87a939bfcd492f056c26e4febe102ea599b5b
* **BUSD**: 0xa5a87a939bfcd492f056c26e4febe102ea599b5b
* **BTC**: 184FDZ1qV2KFzEaNqMefw8UssG8Z57FA6F
* **ETH**: 0xa5a87a939bfcd492f056c26e4febe102ea599b5b
* **SOL**: Gt3bDczPcJvfBeg9TTBrBJGSHLJVkvnSSTov8W3QMpQf

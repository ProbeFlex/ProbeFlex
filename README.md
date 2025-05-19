<p align="center">
  <img src="probe-flex.png" alt="ProbeFlex Logo" width="220"/>
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
| **Integrations**  | Postman collection import, pytest plugin, GitHub Checks annotations.                              |

---

## Architecture

```
             ┌────────────┐
             │  Frontend  │
             └─────┬──────┘
                   │ REST / WebSocket
┌──────────────────┼───────────────────────────────────────────────┐
│              Django API Server                                   │
│  ┌─────────────┴─────────────┐          ┌──────────────────────┐ │
│  │ Request/Test Engine       │  Celery  │ Async Worker Pool    │ │
│  │  • parser / validator     │ <──────> │  • run steps         │ │
│  │  • assertion DSL          │          │  • notify hooks      │ │
│  └─────────────┬─────────────┘          └────────────┬─────────┘ │
│        Sqlite or PostgreSQL           Redis (broker/TTL metrics) │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

* **Backend:** Django 5.2, Django REST Framework, Celery, Redis
* **Database:** Sqlite and PostgreSQL
* **Task Runner:** Celery + Redis (default Redis)

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

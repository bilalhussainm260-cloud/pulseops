# PulseOps — Containerized API Monitoring & Recovery

A hands-on DevOps and Linux operations project demonstrating application containerization, persistent storage, metrics collection, monitoring, alerting, automated testing, CI, and automatic container recovery.

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **Database:** SQLite with Docker volume persistence
- **Containerization:** Docker
- **Monitoring:** Prometheus, Grafana
- **Alerting:** Prometheus alert rules
- **Testing:** pytest
- **CI:** GitHub Actions
- **Version Control:** Git and GitHub

## Architecture

```text
             Client / API Consumer
                      |
                      v
             FastAPI Application
                Port 8000
                      |
             +--------+--------+
             |                 |
             v                 v
        SQLite DB        /prometheus
     Persistent Volume        |
                               v
                         Prometheus
                       Scrape: 15 sec
                               |
                       +-------+-------+
                       |               |
                       v               v
                    Grafana       Alert Rules
                   Dashboards     PulseOpsDown

          GitHub Repository
                  |
                  v
           GitHub Actions
           Tests + Build

          Docker Restart Policy
             unless-stopped
                  |
                  v
         Automatic Crash Recovery
```

## Features

### REST API

PulseOps provides an order-management API with endpoints for creating, retrieving, updating, and deleting orders.

Interactive API documentation is available at:

`http://localhost:8000/docs`

### Persistent Storage

SQLite data is stored using the Docker named volume `pulseops-data`, mounted at `/data`.

The volume allows application data to survive container replacement when the same database path and volume are used.

### Monitoring

Prometheus collects application metrics from:

`http://localhost:8000/prometheus`

The configured scrape interval is 15 seconds.

Grafana provides dashboards for observing API activity and performance.

### Alerting

Prometheus uses the following alert rule:

- **Alert:** `PulseOpsDown`
- **Expression:** `up{job="pulseops"} == 0`
- **Duration:** 30 seconds
- **Severity:** Critical

The alert detects when Prometheus cannot successfully scrape the PulseOps API for the configured duration.

### Automatic Recovery

PulseOps uses Docker's `unless-stopped` restart policy.

Automatic recovery was demonstrated by temporarily introducing a controlled application-crash endpoint, triggering a Uvicorn process exit, and verifying that Docker restarted the application and restored its healthy status without manual intervention.

The temporary crash endpoint was subsequently removed from the application.

### Automated Testing and CI

The project uses pytest for automated application tests.

GitHub Actions runs automated checks and Docker build steps as part of the CI workflow.

## Run with Docker

Build the application:

```bash
docker build -t pulseops:1.7 .
```

Start the API with persistent storage and automatic recovery:

```bash
docker run -d \
  --name pulseops-api \
  --restart unless-stopped \
  -p 8000:8000 \
  -v pulseops-data:/data \
  pulseops:1.7
```

The commands above use Bash-style line continuation. On Windows PowerShell, run the `docker run` command on one line.

Check container status:

```bash
docker ps
```

View logs:

```bash
docker logs pulseops-api
```

## Local Development

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the API:

```bash
python -m uvicorn app.main:app --reload
```

Run tests:

```bash
python -m pytest -q
```

## Verified Project Results

- API container successfully running with Docker health status reported as healthy.
- Prometheus metrics endpoint returned HTTP 200.
- Prometheus successfully scraped the API.
- `PulseOpsDown` alert transitioned to firing during a simulated API outage.
- Automatic container recovery demonstrated following a controlled application crash.
- Four automated tests passed locally.
- GitHub Actions CI checks completed successfully.
- Temporary crash-test endpoint removed and confirmed inaccessible with HTTP 404.

## Scope

PulseOps focuses on local DevOps operations, observability, and container resilience. It does not implement Kubernetes orchestration, Terraform infrastructure provisioning, or AWS deployment.

## Future Improvements

Potential extensions include centralized log aggregation, additional integration tests, and more advanced recovery and alerting scenarios.

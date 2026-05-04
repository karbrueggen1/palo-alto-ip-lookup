# Palo Alto EDL IP Lookup

A web tool to check whether an IPv4 address or network is listed in any of the [Palo Alto EDL (External Dynamic List)](https://docs.paloaltonetworks.com/resources/edl-hosting-service) feeds.

Only Europe, Germany, and Worldwide/Global feeds are checked.

## How it works

On the first request, the tool fetches the feed index from `saasedl.paloaltonetworks.com` and discovers all relevant IPv4 EDL feeds. It then checks the input IP or network against all feeds concurrently and returns every feed that contains a match, including the matching subnets.

The feed list is cached in memory for the lifetime of the process.

## Usage

Enter an IPv4 address or CIDR network in the input field and click **Lookup**:

- Single address: `52.123.224.73`
- Network: `52.123.224.0/24`

The result shows all EDL feeds the IP was found in, along with the matching subnets and the feed URL.

## Deployment

**Prerequisites:** Docker and Docker Compose.

```bash
docker compose up -d
```

The app is then available at `http://localhost:8080`.

To rebuild after code changes:

```bash
docker compose up -d --build
```

## Local development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

The dev server starts on `http://localhost:5000`.

## Configuration

| Environment variable | Default | Description |
|---|---|---|
| `FLASK_ENV` | — | Set to `production` for production deployments |

The rate limit is 30 requests per minute per IP address.

## Tech stack

- Python 3.12, Flask
- BeautifulSoup4 (feed discovery)
- `concurrent.futures.ThreadPoolExecutor` (parallel feed checks)
- Docker / Docker Compose

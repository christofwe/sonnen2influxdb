# sonnen2influxdb

Simple container that queries your sonnenBatterie's(https://sonnen.de/) API and writes metrics to an influxDB.

## Requirements:
- Docker execution runtime
- sonnenBatterie

## Steps
1. Copy `.env.sample` to `.env` and update w/ actual values
2. Run `docker-compose up -d`
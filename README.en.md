🇪🇸 [Español](README.md) · 🇬🇧 **English**

# Data Engineering and Cloud Portfolio

Streaming, orchestration, modern data stack, serverless, Kubernetes and an Iceberg lakehouse, run locally with Docker and
with infrastructure as code ready for the cloud.

**Main tools:** Docker · Spark · Airflow · Dagster · dbt · Kubernetes · Terraform · Iceberg · PostgreSQL · LightGBM · FastAPI · Power BI

Each folder is an independent project with its own README (results first), step-by-step guide, automated tests and
reproduction instructions. Raw data are not versioned: every project ships a script that downloads them from the official
source.

> 🌐 The English pages of the observatory are a full translation; the other projects have an English summary with the key
> results. Guides and code comments are in Spanish.

## Featured project

**[📊 Ecuador Labor Observatory](observatorio-laboral-ec/README.en.md)**: from the microdata of Ecuador's employment survey
to a model in production. **Live:** [app with simulator](https://observatorio-laboral-ec.streamlit.app/?lang=en) ·
[public dashboard (Spanish)](https://datastudio.google.com/reporting/a932a4c2-ecc6-4148-afd1-df75157ebdb0).

## Projects

| Project | What it is about |
|---|---|
| [**📊 Ecuador Labor Observatory · ENEMDU → dbt → ML → Power BI**](observatorio-laboral-ec/README.en.md) ⭐ | End-to-end integrative project: automated ingestion into PostgreSQL (Neon), dbt with 40 tests, official rates reproduced, Power BI, explainable LightGBM model (AUC 0.91), forecast with backtesting, Dockerized API, drift monitor and weekly pipeline |
| [**Daily ingestion of public APIs with Apache Airflow · Ecuador's climate + World Bank**](airflow-apis-postgres/README.en.md) | Three Airflow 3.3 DAGs on Docker Compose bring daily weather for 13 Ecuadorian cities and 10 World Bank indicators into Postgres, with a real backfill and quality checks that stop the DAG |
| [**☁️ Ecuador climate API on Kubernetes · FastAPI, Helm and observability**](kubernetes-api-clima/README.en.md) | FastAPI and Streamlit on a local kind cluster with Helm, Ingress, HPA, Prometheus and Grafana, with measured load tests |
| [**🧊 Local lakehouse with Apache Iceberg + Trino + Nessie on Wikipedia pageviews**](lakehouse-iceberg-trino-nessie/README.en.md) | MinIO, Nessie, Trino and PyIceberg: time travel, schema and partition evolution, compaction and write-audit-publish with branches |
| [**🌦️ Local modern data stack: Dagster + dbt + DuckDB + MinIO on NOAA GHCN-Daily**](modern-data-stack-dagster-dbt/README.en.md) | Asset-based pipeline over 177.5 million daily observations from ~45,000 weather stations |
| [**🌎 Serverless earthquake alerts · USGS → S3 → Lambda → DynamoDB → SNS**](serverless-sismos-localstack/README.en.md) | Event-driven pipeline deployed with Terraform on LocalStack, with idempotent writes and measured latencies |
| [**Real-time streaming of GitHub activity · Redpanda + Spark Structured Streaming + Delta Lake**](streaming-github-redpanda-spark/README.en.md) | 11.4 million public GitHub events through bronze, silver and gold layers, exactly once, tested with `docker kill` |

## How to use this repository

```bash
git clone https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD.git
cd PORTAFOLIO-CLOUD/<project>
```

Inside each project, follow the reproduction section of its README and `docs/GUIA_PASO_A_PASO.md` (Spanish).

## Author

**Erick Guarnizo** · [LinkedIn](https://www.linkedin.com/in/erick-g-571a7b3b4)

## License

Code is under the [MIT](LICENSE) license. Each project's data keep the license of their source, stated in its README.

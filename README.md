🇺🇸 **English** · 🇪🇸 [Español](README.es.md)

# Data engineering and cloud portfolio

Seven projects: an automated data platform, streaming, orchestration, a lakehouse, an asset-based stack, serverless and Kubernetes.
Each one has code, tests, a CI workflow and results measured in a real run.

| Measured result | Project | Evidence |
|---|---|---|
| **20 of 20** official rates reproduced by a weekly pipeline, 40 dbt tests | [Ecuador Labor Observatory](observatorio-laboral-ec/README.md) | [Runs](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions/workflows/observatorio-laboral-ec-pipeline.yml) |
| **0 duplicates and 0 lost** in bronze and silver after 3 `docker kill` (2.9 million messages); main run with 11.4 million events | [GitHub activity streaming](streaming-github-redpanda-spark/README.md) | [Recovery](streaming-github-redpanda-spark/reports/metricas/recuperacion/verificacion.json) · [main run](streaming-github-redpanda-spark/reports/metricas/principal/verificacion.json) |
| **410** backfill runs and 6,405 logged quality checks | [Scheduled ingestion with Airflow](airflow-apis-postgres/README.md) | [Results](airflow-apis-postgres/reports/resultados.json) |
| **3 of 7** checks fail on a defective day, and `main` does not change (write-audit-publish) | [Lakehouse](lakehouse-iceberg-trino-nessie/README.md) | [Branches](lakehouse-iceberg-trino-nessie/reports/iceberg/05_ramas_nessie.json) |
| **0 errors in 39,842 requests** during a rolling upgrade | [Climate API on Kubernetes](kubernetes-api-clima/README.md) | [Upgrade](kubernetes-api-clima/reports/rolling_update.json) |

## Start here

| If you are looking for… | Go to |
|---|---|
| **Data engineering** | [Observatory](observatorio-laboral-ec/README.md): dbt and a weekly pipeline · [Streaming](streaming-github-redpanda-spark/README.md): Spark and Delta · [Airflow](airflow-apis-postgres/README.md): backfills and quality |
| **Cloud and DevOps** | [Kubernetes](kubernetes-api-clima/README.md): Helm, HPA, Prometheus · [Serverless](serverless-sismos-localstack/README.md): Terraform, Lambda, LocalStack |
| **A live demo** | [Ecuador Labor Observatory app](https://observatorio-laboral-ec.streamlit.app/?lang=en) ([project](observatorio-laboral-ec/README.md)) |
| **CI and automation** | [Workflows](.github/workflows) · [runs](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions) |
| **Infrastructure as code** | [AWS serverless](serverless-sismos-localstack/terraform) · [AWS lakehouse](lakehouse-iceberg-trino-nessie/terraform/aws) · [AWS streaming](streaming-github-redpanda-spark/infra/terraform/aws) · [GCP](modern-data-stack-dagster-dbt/terraform/gcp) |
| **Design decisions** | [Observatory ADRs](observatorio-laboral-ec/docs/adr) (Spanish) and the decisions section of each full README |

## Projects

| Project | What it is | CI | Tests |
|---|---|---|---|
| [Ecuador Labor Observatory](observatorio-laboral-ec/README.md) (featured) | Survey microdata to PostgreSQL, dbt, a containerized API, a public app and a drift monitor | [![CI](https://img.shields.io/github/actions/workflow/status/GUAR-NIX/PORTAFOLIO-CLOUD/observatorio-laboral-ec.yml?branch=main&label=CI)](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions/workflows/observatorio-laboral-ec.yml) | [tests](observatorio-laboral-ec/tests) |
| [GitHub activity streaming](streaming-github-redpanda-spark/README.md) | Redpanda, Spark Structured Streaming and Delta Lake, exactly once | [![CI](https://img.shields.io/github/actions/workflow/status/GUAR-NIX/PORTAFOLIO-CLOUD/streaming-github-redpanda-spark.yml?branch=main&label=CI)](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions/workflows/streaming-github-redpanda-spark.yml) | [tests](streaming-github-redpanda-spark/tests) |
| [Scheduled ingestion with Airflow](airflow-apis-postgres/README.md) | Three Airflow 3.3 DAGs load weather for 13 cities and 10 World Bank indicators into PostgreSQL, with quality checks that stop the DAG | [![CI](https://img.shields.io/github/actions/workflow/status/GUAR-NIX/PORTAFOLIO-CLOUD/airflow-apis-postgres.yml?branch=main&label=CI)](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions/workflows/airflow-apis-postgres.yml) | [tests](airflow-apis-postgres/tests) |
| [Lakehouse with Iceberg, Trino and Nessie](lakehouse-iceberg-trino-nessie/README.md) | Time travel, schema and partition evolution, compaction and write-audit-publish with branches | [![CI](https://img.shields.io/github/actions/workflow/status/GUAR-NIX/PORTAFOLIO-CLOUD/lakehouse-iceberg-trino-nessie.yml?branch=main&label=CI)](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions/workflows/lakehouse-iceberg-trino-nessie.yml) | [tests](lakehouse-iceberg-trino-nessie/tests) |
| [Data stack with Dagster and dbt](modern-data-stack-dagster-dbt/README.md) | Asset-based pipeline over 177.5 million daily observations from about 45,000 weather stations | [![CI](https://img.shields.io/github/actions/workflow/status/GUAR-NIX/PORTAFOLIO-CLOUD/modern-data-stack-dagster-dbt.yml?branch=main&label=CI)](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions/workflows/modern-data-stack-dagster-dbt.yml) | [tests](modern-data-stack-dagster-dbt/tests) |
| [Serverless earthquake alerts](serverless-sismos-localstack/README.md) | S3, Lambda, DynamoDB and SNS deployed with Terraform on LocalStack, with idempotent writes | [![CI](https://img.shields.io/github/actions/workflow/status/GUAR-NIX/PORTAFOLIO-CLOUD/serverless-sismos-localstack.yml?branch=main&label=CI)](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions/workflows/serverless-sismos-localstack.yml) | [tests](serverless-sismos-localstack/tests) |
| [Climate API on Kubernetes](kubernetes-api-clima/README.md) | FastAPI and Streamlit on a local kind cluster with Helm, Ingress, HPA, Prometheus and Grafana, with measured load tests | [![CI](https://img.shields.io/github/actions/workflow/status/GUAR-NIX/PORTAFOLIO-CLOUD/kubernetes-api-clima.yml?branch=main&label=CI)](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions/workflows/kubernetes-api-clima.yml) | [tests](kubernetes-api-clima/tests) |

## What was deployed and what was not

- **Public:** the observatory app, its dashboard and its weekly pipeline, on free cloud tiers.
- **Local or emulated:** everything else runs on Docker, kind or LocalStack. Terraform for AWS and GCP in the lakehouse, streaming
  and Dagster projects is validated in CI and was never applied; cost figures are estimates.
- Load and latency figures come from a laptop and are not production capacity.

## How to use this repository

```bash
git clone https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD.git
cd PORTAFOLIO-CLOUD/<project>
```

Inside each project, follow the reproduction section of its README and `docs/GUIA_PASO_A_PASO.md` (Spanish). Raw data are not
versioned: every project has a script that gets them from the official source. The observatory page is in English in full; the other
projects have an English summary and a full README in Spanish.

## Author

**Erick Guarnizo** · [LinkedIn](https://www.linkedin.com/in/erick-g-571a7b3b4) · [GitHub profile](https://github.com/GUAR-NIX)

## License

Code is under the [MIT](LICENSE) license. Each project's data keep the license of their source, stated in its README.

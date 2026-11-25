"""Se ejecuta una sola vez al construir la imagen: Ivy resuelve los conectores de Spark (Kafka, Delta, S3A) y se
copian a la carpeta jars/ de PySpark. Así los jobs arrancan sin red y sin `spark.jars.packages`.

Si Maven Central falla al servir un .pom (p. ej. "Connection refused" pasajero), Ivy da el conector por resuelto
pero sin sus dependencias y Spark no avisa: la imagen se construiría sin kafka-clients y el pipeline moriría al
arrancar con NoClassDefFoundError. Por eso se comprueba que estén los jars imprescindibles, se repite la
resolución hasta 3 veces y, si aun así faltan, la construcción falla con un mensaje claro.

Si Maven Central no sirve ningún conector, spark-submit termina con error: también cuenta como intento fallido.
Desde el segundo intento se añade el espejo de Maven Central en Google Cloud."""

import shutil
import subprocess
import sys
import time
from pathlib import Path

import pyspark

PAQUETES = [
    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3",
    "io.delta:delta-spark_2.12:3.2.1",
    "org.apache.hadoop:hadoop-aws:3.3.4",  # misma versión de Hadoop que trae PySpark 3.5.3
]
# Lo que el pipeline necesita en el classpath (directos y transitivos de los paquetes de arriba).
IMPRESCINDIBLES = [
    "spark-sql-kafka-0-10_2.12-", "spark-token-provider-kafka-0-10_2.12-", "kafka-clients-", "commons-pool2-",
    "delta-spark_2.12-", "delta-storage-", "hadoop-aws-", "aws-java-sdk-bundle-",
]
IVY = Path("/tmp/ivy")
INTENTOS = 3
ESPEJO = "https://maven-central.storage-download.googleapis.com/maven2/"


def resolver(con_espejo: bool) -> list[Path]:
    """Resuelve en un proceso nuevo: spark.jars.packages solo se lee al lanzar la JVM."""
    shutil.rmtree(IVY, ignore_errors=True)
    espejo = f".config('spark.jars.repositories', {ESPEJO!r})" if con_espejo else ""
    codigo = (
        "from pyspark.sql import SparkSession; "
        f"SparkSession.builder.master('local[1]').config('spark.jars.packages', {','.join(PAQUETES)!r})"
        f".config('spark.jars.ivy', {str(IVY)!r}){espejo}.getOrCreate().stop()"
    )
    # Sin check=True: si falla, los jars que faltan hacen que se repita el intento.
    subprocess.run([sys.executable, "-c", codigo], check=False)
    return sorted((IVY / "jars").glob("*.jar"))


for intento in range(1, INTENTOS + 1):
    jars = resolver(con_espejo=intento > 1)
    faltan = [j for j in IMPRESCINDIBLES if not any(j in p.name for p in jars)]
    if not faltan:
        break
    print(f"Intento {intento}/{INTENTOS}: Ivy no resolvió {faltan} (fallo de red con Maven).")
    if intento < INTENTOS:
        time.sleep(15 * intento)
else:
    raise SystemExit(f"No se pudieron resolver los conectores de Spark: faltan {faltan}. "
                     "Revisa la conexión y vuelve a ejecutar `docker compose build`.")

destino = Path(pyspark.__file__).parent / "jars"
copiados = 0
for jar in jars:
    # Ivy nombra los jars "grupo_artefacto-versión.jar"; PySpark ya trae algunos (lz4, snappy, hadoop-client...)
    # como "artefacto-versión.jar": no se copian para no tener la misma clase dos veces en el classpath.
    nombre = jar.name.split("_", 1)[-1]
    if not (destino / nombre).exists():
        shutil.copy2(jar, destino / nombre)
        copiados += 1
        print("  +", jar.name)
shutil.rmtree(IVY)
print(f"{copiados} jars copiados a {destino}")

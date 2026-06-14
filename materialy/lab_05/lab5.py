"""
Analiza Przestępczości w Chicago — PySpark
==========================================
Zbiór: Chicago Crimes (~50 000 ostatnich zdarzeń)

Realizuje:
  1. Wczytanie i czyszczenie danych (duplikaty, braki, błędne daty)
  2. UDF klasyfikujący porę dnia na podstawie godziny
  3. Optymalizacja: cache(), broadcast join, zapis do Parquet partycjonowany po roku
  4. Analiza statystyczna + plan zapytania (.explain) najcięższej agregacji
  5. (Opcjonalnie) Model wieloklasowy MLlib przewidujący typ przestępstwa

Uruchomienie:
    spark-submit lab5.py
albo w notebooku — uruchom sekcje po kolei.

Uwaga o schemacie: kolumny zbioru Chicago Crimes mają spacje
('Primary Type', 'Location Description', 'Date'), a format daty to
'MM/dd/yyyy hh:mm:ss a' (12-godzinny z AM/PM). Jeśli Twój plik różni się
nagłówkiem lub formatem daty — dostosuj stałe CSV_PATH i DATE_FORMAT poniżej.
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import broadcast
from pyspark.sql.types import StringType

from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

# --- Konfiguracja ---------------------------------------------------------
CSV_PATH = "chicago_crimes_sample.csv"
DATE_FORMAT = "MM/dd/yyyy hh:mm:ss a"          
PARQUET_OUT = "output/chicago_crimes_parquet"
RUN_ML = True                                   

# --- UDF: pora dnia -------------------------------------------------------
def time_of_day(hour):
    """Klasyfikuje godzinę (0-23) na porę dnia."""
    if hour is None:
        return "nieznana"
    if 5 <= hour < 12:
        return "rano"
    elif 12 <= hour < 17:
        return "dzień"
    elif 17 <= hour < 22:
        return "wieczór"
    else:
        return "noc"


def main():
    spark = (
        SparkSession.builder
        .appName("ChicagoCrimes")
        .config("spark.sql.shuffle.partitions", "8")  
        .getOrCreate()
    )

    # =====================================================================
    # 1. WCZYTANIE I CZYSZCZENIE
    # =====================================================================
    df_raw = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(CSV_PATH)
    )

    
    df = df_raw.withColumn(
        "Date_parsed",
        F.to_timestamp(F.col("Date"), DATE_FORMAT)
    )

    key_cols = ["ID", "Primary Type", "Date_parsed", "Latitude", "Longitude"]

    df_clean = (
        df
        .dropDuplicates(["ID"])                      
        .na.drop(subset=key_cols)                   
        .filter(F.col("Date_parsed").isNotNull())    
        .filter(
            (F.year("Date_parsed") >= 2001) &
            (F.year("Date_parsed") <= F.year(F.current_date()))  
        )
        .withColumn("Year", F.year("Date_parsed"))
        .withColumn("Hour", F.hour("Date_parsed"))
    )

    print(f"Wierszy przed: {df.count()}, po czyszczeniu: {df_clean.count()}")

    # =====================================================================
    # 2. UDF — PORA DNIA na podstawie godziny
    # =====================================================================
    time_of_day_udf = F.udf(time_of_day, StringType())
    df_clean = df_clean.withColumn("TimeOfDay", time_of_day_udf(F.col("Hour")))

    
    df_clean.cache()
    df_clean.show(5)

    # =====================================================================
    # 3. OPTYMALIZACJA: broadcast join + zapis Parquet partycjonowany
    # =====================================================================
    kategorie = spark.createDataFrame(
        [
            ("THEFT", "własność"), ("BURGLARY", "własność"),
            ("MOTOR VEHICLE THEFT", "własność"),
            ("BATTERY", "przemoc"), ("ASSAULT", "przemoc"), ("HOMICIDE", "przemoc"),
            ("NARCOTICS", "narkotyki"),
        ],
        ["Primary Type", "Kategoria"],
    )

    df_kat = df_clean.join(broadcast(kategorie), on="Primary Type", how="left")
    df_kat = df_kat.fillna({"Kategoria": "inne"})

    
    (
        df_kat.write
        .mode("overwrite")
        .partitionBy("Year")
        .parquet(PARQUET_OUT)
    )
    print(f"Zapisano dane do: {PARQUET_OUT} (partycjonowane wg Year)")

    # =====================================================================
    # 4. ANALIZA + EXPLAIN najcięższej agregacji
    # =====================================================================
    print("\n=== Najpopularniejsze typy przestępstw ===")
    (
        df_clean.groupBy("Primary Type").count()
        .orderBy(F.desc("count"))
        .show(10, truncate=False)
    )

    agg = (
        df_clean
        .groupBy("Location Description", "TimeOfDay", "Primary Type")
        .count()
        .orderBy(F.desc("count"))
    )

    print("=== Typ × lokalizacja × pora dnia ===")
    agg.show(15, truncate=False)

    print("=== PLAN ZAPYTANIA NAJCIĘŻSZEJ AGREGACJI ===")
    agg.explain(mode="formatted")

    # =====================================================================
    # 5. (Opcjonalnie) MODEL WIELOKLASOWY — MLlib
    # =====================================================================
    if RUN_ML:
        print("\n=== Trening modelu klasyfikacji (MLlib) ===")


        top_types = [
            r["Primary Type"] for r in
            df_clean.groupBy("Primary Type").count()
            .orderBy(F.desc("count")).limit(5).collect()
        ]

        ml_df = (
            df_clean
            .filter(F.col("Primary Type").isin(top_types))
            .withColumn("Arrest_int", F.col("Arrest").cast("boolean").cast("int"))
            .na.drop(subset=["Location Description", "Hour", "Arrest_int"])
        )

        loc_idx = StringIndexer(
            inputCol="Location Description", outputCol="loc_idx", handleInvalid="keep"
        )
        loc_ohe = OneHotEncoder(inputCol="loc_idx", outputCol="loc_vec")
        label_idx = StringIndexer(inputCol="Primary Type", outputCol="label")
        assembler = VectorAssembler(
            inputCols=["loc_vec", "Hour", "Arrest_int"], outputCol="features"
        )
        rf = RandomForestClassifier(
            featuresCol="features", labelCol="label", numTrees=30
        )

        pipeline = Pipeline(stages=[loc_idx, loc_ohe, label_idx, assembler, rf])

        train, test = ml_df.randomSplit([0.8, 0.2], seed=42)
        model = pipeline.fit(train)
        pred = model.transform(test)

        evaluator = MulticlassClassificationEvaluator(
            labelCol="label", predictionCol="prediction", metricName="accuracy"
        )
        print(f"Dokładność modelu: {evaluator.evaluate(pred):.3f}")

    # --- Sprzątanie -------------------------------------------------------
    df_clean.unpersist()
    spark.stop()


if __name__ == "__main__":
    main()
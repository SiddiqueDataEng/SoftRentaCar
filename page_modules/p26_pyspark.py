"""
p26_pyspark.py — PySpark & Databricks Learning Platform
Complete guide: RDDs, DataFrames, SQL, Streaming, Delta Lake,
MLlib, performance tuning, Databricks platform features.
Live code examples using pandas equivalents that run in browser.
"""
import io, contextlib
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from page_modules._shared import inject, get_data, BRAND, STEEL, GREEN, AMBER, ORANGE, TEXT
inject()
M="#5a7a96"; CB="#141e2b"; BD="#1e2f44"; TEAL="#2A9D8F"; PUR="#6A4C93"
def _card(b,l=BRAND,p="14px 16px"): return f'<div style="background:{CB};border:1px solid {BD};border-left:3px solid {l};border-radius:10px;padding:{p};margin:6px 0;">{b}</div>'
def _h2(t,i=""): return f'<div style="font-size:1.22rem;font-weight:800;color:{TEXT};margin:16px 0 4px;"><span style="color:{BRAND};">{i} </span>{t}</div>'
def _h3(t,c=STEEL): return f'<div style="font-size:.9rem;font-weight:700;color:{c};border-left:3px solid {c};padding-left:8px;margin:10px 0 6px;">{t}</div>'
def _run_pandas(code, dfs):
    """Run code with pandas equivalent (real execution)."""
    buf = io.StringIO()
    ns  = {"dfs":dfs,"pd":pd,"np":np,"result":None}
    with contextlib.redirect_stdout(buf):
        try: exec(compile(code,"<spark>","exec"),ns)
        except Exception as e: print(f"Error: {e}")
    return buf.getvalue(), ns.get("result")

dfs = get_data()

st.markdown(
    f'<div style="font-size:1.6rem;font-weight:900;color:{BRAND};">⚡ PySpark & Databricks</div>'
    f'<div style="font-size:.8rem;color:{M};">Architecture · DataFrames · SQL · Streaming · Delta Lake · MLlib · Performance · Databricks</div>',
    unsafe_allow_html=True)
st.markdown(f"<hr style='border-color:{BD};margin:6px 0 10px'>",unsafe_allow_html=True)
st.info("PySpark code is shown for learning. Each example also includes a runnable pandas equivalent.", icon="ℹ️")

TAB = st.tabs([
    "🏗️ Architecture",
    "📊 DataFrames",
    "🔗 Joins & Aggregations",
    "🪟 Window Functions",
    "📡 Streaming",
    "🔷 Delta Lake",
    "🤖 MLlib",
    "⚡ Performance",
    "🏭 Databricks",
    "💻 Live Lab",
])

# ── TAB 0: ARCHITECTURE ──────────────────────────────────────────────────────
with TAB[0]:
    st.markdown(_h2("Spark Architecture","🏗️"), unsafe_allow_html=True)
    arch_items = [
        ("Driver Program","The main Python/JVM process. Creates SparkContext, defines transformations/actions, orchestrates workers.",BRAND),
        ("SparkContext","Entry point for Spark functionality. Creates RDDs, connects to cluster manager.",TEAL),
        ("Cluster Manager","Manages worker nodes. Options: Spark Standalone, YARN (Hadoop), Mesos, Kubernetes.",AMBER),
        ("Executor","JVM process on each worker node. Runs tasks, stores data in memory/disk.",STEEL),
        ("Task","Smallest unit of work. Runs on one partition. One task per partition per stage.",PUR),
        ("Stage","A set of tasks with no shuffle between them. Shuffle creates a stage boundary.",ORANGE),
        ("Job","Triggered by an ACTION (count, show, write). One job = one DAG execution.",BRAND),
        ("DAG","Directed Acyclic Graph of stages. Catalyst optimizer creates this from your transformations.",TEAL),
    ]
    c1,c2 = st.columns(2)
    for i,(t,d,c) in enumerate(arch_items):
        (c1 if i%2==0 else c2).markdown(_card(f'<b style="color:{c};font-size:.82rem;">{t}</b><br><span style="font-size:.74rem;color:{TEXT};">{d}</span>',l=c,p="9px 12px"), unsafe_allow_html=True)

    st.markdown(_h3("Transformations vs Actions",STEEL), unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown(_card(f'<b style="color:{TEAL};">Transformations (LAZY)</b><br>'
                          f'<span style="font-size:.75rem;color:{TEXT};">Return new DataFrame. Do not execute.<br>'
                          f'• filter(), select(), withColumn()<br>• groupBy(), join(), orderBy()<br>• map(), flatMap(), union()<br>• Narrow: no shuffle<br>• Wide: causes shuffle</span>',l=TEAL,p="10px 14px"), unsafe_allow_html=True)
    with c2:
        st.markdown(_card(f'<b style="color:{BRAND};">Actions (EAGER)</b><br>'
                          f'<span style="font-size:.75rem;color:{TEXT};">Trigger execution. Return values or write.<br>'
                          f'• show(), count(), collect()<br>• write.parquet(), saveAsTable()<br>• first(), take(n)<br>• reduce(), foreach()<br>• Each action triggers a new Spark Job</span>',l=BRAND,p="10px 14px"), unsafe_allow_html=True)

    st.code("""# Spark execution model
trips = spark.read.parquet("trips.parquet")   # no execution
filtered = trips.filter(trips.status == "Completed")  # no execution
grouped = filtered.groupBy("fleet_id").sum("trip_fare_pkr")  # no execution

# This ACTION triggers execution:
grouped.show()  # Spark builds DAG, optimises, executes

# Caching: avoid re-reading source for multiple actions
filtered.cache()   # stores in memory after first computation
filtered.count()   # populates cache
filtered.show()    # reads from cache (fast!)""", language="python")

# ── TAB 1: DATAFRAMES ────────────────────────────────────────────────────────
with TAB[1]:
    st.markdown(_h2("PySpark DataFrames","📊"), unsafe_allow_html=True)
    _df_examples = {
        "Read & inspect": {
            "spark": """from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("RentACar").getOrCreate()
df = spark.read.csv("trips.csv", header=True, inferSchema=True)
df.printSchema()
df.show(5)
print(f"Rows: {df.count()}, Cols: {len(df.columns)}")""",
            "pandas": """trips = dfs["trips"].copy()
print(trips.dtypes)
result = trips.head(5)
print(f"Shape: {trips.shape}")""",
        },
        "Filter & Select": {
            "spark": """from pyspark.sql import functions as F
completed = df.filter(F.col("status") == "Completed")
result = completed.select("trip_id","pickup_city","trip_fare_pkr") \\
                  .orderBy(F.col("trip_fare_pkr").desc()) \\
                  .limit(10)
result.show()""",
            "pandas": """trips = dfs["trips"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"],errors="coerce").fillna(0)
result = (trips[trips["status"]=="Completed"][["trip_id","pickup_city","trip_fare_pkr"]]
          .nlargest(10,"trip_fare_pkr"))
print(result.to_string(index=False))""",
        },
        "withColumn / derived columns": {
            "spark": """from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

df_enriched = df.withColumn("trip_fare_pkr", F.col("trip_fare_pkr").cast(DoubleType())) \\
    .withColumn("pickup_datetime", F.to_timestamp("pickup_datetime")) \\
    .withColumn("dropoff_datetime", F.to_timestamp("dropoff_datetime")) \\
    .withColumn("duration_hrs",
        (F.unix_timestamp("dropoff_datetime") - F.unix_timestamp("pickup_datetime")) / 3600) \\
    .withColumn("is_intercity",
        (F.col("pickup_city") != F.col("dropoff_city")).cast("boolean")) \\
    .withColumn("fare_tier",
        F.when(F.col("trip_fare_pkr") < 5000, "Budget")
         .when(F.col("trip_fare_pkr") < 15000, "Economy")
         .when(F.col("trip_fare_pkr") < 50000, "Standard")
         .otherwise("Premium"))
df_enriched.select("trip_id","duration_hrs","is_intercity","fare_tier").show(5)""",
            "pandas": """trips = dfs["trips"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"],errors="coerce").fillna(0)
trips["pickup_datetime"] = pd.to_datetime(trips["pickup_datetime"],errors="coerce")
trips["dropoff_datetime"] = pd.to_datetime(trips["dropoff_datetime"],errors="coerce")
trips["duration_hrs"] = (trips["dropoff_datetime"]-trips["pickup_datetime"]).dt.total_seconds()/3600
trips["is_intercity"] = trips["pickup_city"] != trips["dropoff_city"]
def fare_tier(x):
    if x<5000: return "Budget"
    elif x<15000: return "Economy"
    elif x<50000: return "Standard"
    else: return "Premium"
trips["fare_tier"] = trips["trip_fare_pkr"].apply(fare_tier)
result = trips[["trip_id","duration_hrs","is_intercity","fare_tier"]].head(8)
print(result.to_string(index=False))""",
        },
    }

    for ex_name, ex in _df_examples.items():
        with st.expander(f"**{ex_name}**"):
            c1,c2 = st.columns(2)
            with c1:
                st.markdown(f'<div style="font-size:.76rem;font-weight:700;color:{BRAND};">PySpark</div>', unsafe_allow_html=True)
                st.code(ex["spark"], language="python")
            with c2:
                st.markdown(f'<div style="font-size:.76rem;font-weight:700;color:{TEAL};">pandas equivalent (runs here)</div>', unsafe_allow_html=True)
                st.code(ex["pandas"], language="python")
                if st.button(f"▶ Run pandas", key=f"df_run_{hash(ex_name)}"):
                    out, res = _run_pandas(ex["pandas"], dfs)
                    if out: st.code(out, language="text")
                    if isinstance(res, pd.DataFrame): st.dataframe(res, use_container_width=True, height=200, hide_index=True)

# ── TAB 2: JOINS & AGGREGATIONS ──────────────────────────────────────────────
with TAB[2]:
    st.markdown(_h2("Joins & Aggregations in PySpark","🔗"), unsafe_allow_html=True)
    JOIN_EXAMPLES = {
        "Revenue by fleet (groupBy + agg)": {
            "spark": """from pyspark.sql import functions as F
result = (df.filter(F.col("status")=="Completed")
            .groupBy("fleet_id")
            .agg(
                F.count("trip_id").alias("trips"),
                F.round(F.sum("trip_fare_pkr"),0).alias("revenue_pkr"),
                F.round(F.avg("trip_fare_pkr"),0).alias("avg_fare"),
            )
            .orderBy(F.col("revenue_pkr").desc()))
result.show()""",
            "pandas": """trips = dfs["trips"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"],errors="coerce").fillna(0)
result = (trips[trips["status"]=="Completed"]
          .groupby("fleet_id")
          .agg(trips=("trip_id","count"),revenue_pkr=("trip_fare_pkr","sum"),avg_fare=("trip_fare_pkr","mean"))
          .round(0).sort_values("revenue_pkr",ascending=False).reset_index())
print(result.to_string(index=False))""",
        },
        "Join trips with customers": {
            "spark": """from pyspark.sql import functions as F
trips = spark.read.csv("trips.csv", header=True, inferSchema=True)
customers = spark.read.csv("customers.csv", header=True, inferSchema=True)
result = (trips.alias("t")
               .join(customers.alias("c"), on="customer_id", how="inner")
               .filter(F.col("t.status")=="Completed")
               .select("t.trip_id","c.full_name","c.city","t.trip_fare_pkr")
               .orderBy(F.col("t.trip_fare_pkr").desc())
               .limit(10))
result.show()""",
            "pandas": """trips = dfs["trips"].copy()
custs = dfs["customers"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"],errors="coerce").fillna(0)
merged = trips[trips["status"]=="Completed"].merge(
    custs[["customer_id","full_name","city"]], on="customer_id")
result = merged[["trip_id","full_name","city","trip_fare_pkr"]].nlargest(10,"trip_fare_pkr")
print(result.to_string(index=False))""",
        },
        "Broadcast join for small table": {
            "spark": """from pyspark.sql import functions as F
from pyspark.sql.functions import broadcast

# fleets is small (~5 rows) — broadcast it!
trips = spark.read.csv("trips.csv", header=True, inferSchema=True)
fleets = spark.read.csv("fleets.csv", header=True, inferSchema=True)

result = trips.join(broadcast(fleets), on="fleet_id", how="left") \\
              .select("trip_id","fleet_name","city","trip_fare_pkr") \\
              .limit(10)
result.show()
# Broadcast hint prevents shuffle — critical for skewed joins!""",
            "pandas": """trips = dfs["trips"].copy()
fleets = dfs["fleets"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"],errors="coerce").fillna(0)
result = trips.merge(fleets[["fleet_id","fleet_name","city"]], on="fleet_id", how="left")
result = result[["trip_id","fleet_name","city","trip_fare_pkr"]].head(8)
print(result.to_string(index=False))""",
        },
    }
    for ex_name, ex in JOIN_EXAMPLES.items():
        with st.expander(f"**{ex_name}**"):
            c1,c2 = st.columns(2)
            with c1:
                st.markdown(f'<div style="font-size:.76rem;font-weight:700;color:{BRAND};">PySpark</div>', unsafe_allow_html=True)
                st.code(ex["spark"], language="python")
            with c2:
                st.markdown(f'<div style="font-size:.76rem;font-weight:700;color:{TEAL};">pandas (runs)</div>', unsafe_allow_html=True)
                st.code(ex["pandas"], language="python")
                if st.button("▶ Run", key=f"join_run_{hash(ex_name)}"):
                    out, res = _run_pandas(ex["pandas"], dfs)
                    if out: st.code(out, language="text")
                    if isinstance(res, pd.DataFrame): st.dataframe(res, use_container_width=True, height=200, hide_index=True)

# ── TAB 3: WINDOW FUNCTIONS ──────────────────────────────────────────────────
with TAB[3]:
    st.markdown(_h2("Window Functions in PySpark","🪟"), unsafe_allow_html=True)
    st.code("""from pyspark.sql import functions as F
from pyspark.sql.window import Window

trips = spark.read.csv("trips.csv", header=True, inferSchema=True)

# Window specs
w_fleet = Window.partitionBy("fleet_id").orderBy("pickup_datetime")
w_fleet_unb = Window.partitionBy("fleet_id").orderBy("pickup_datetime").rowsBetween(
    Window.unboundedPreceding, Window.currentRow)
w_month = Window.orderBy("month").rowsBetween(-2, 0)  # 3-month rolling

result = trips.filter(F.col("status")=="Completed").select(
    "trip_id","fleet_id","pickup_datetime","trip_fare_pkr",

    # Ranking
    F.row_number().over(w_fleet).alias("trip_seq"),
    F.rank().over(w_fleet.orderBy(F.col("trip_fare_pkr").desc())).alias("fare_rank"),
    F.ntile(4).over(Window.orderBy("trip_fare_pkr")).alias("fare_quartile"),

    # Navigation
    F.lag("trip_fare_pkr",1).over(w_fleet).alias("prev_fare"),
    F.lead("trip_fare_pkr",1).over(w_fleet).alias("next_fare"),

    # Running totals
    F.sum("trip_fare_pkr").over(w_fleet_unb).alias("fleet_cumulative_rev"),
    F.avg("trip_fare_pkr").over(w_fleet_unb).alias("fleet_rolling_avg"),
)
result.show(10)""", language="python")

    st.markdown(_h3("Pandas equivalent (runs here)",TEAL), unsafe_allow_html=True)
    if st.button("▶ Run Window Functions Demo", key="wf_spark"):
        _code = """
trips = dfs["trips"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"],errors="coerce").fillna(0)
trips["pickup_datetime"] = pd.to_datetime(trips["pickup_datetime"],errors="coerce")
c = trips[trips["status"]=="Completed"].sort_values(["fleet_id","pickup_datetime"])
c["trip_seq"] = c.groupby("fleet_id").cumcount()+1
c["prev_fare"] = c.groupby("fleet_id")["trip_fare_pkr"].shift(1)
c["fleet_cum_rev"] = c.groupby("fleet_id")["trip_fare_pkr"].cumsum()
c["fare_quartile"] = pd.qcut(c["trip_fare_pkr"],4,labels=[1,2,3,4],duplicates="drop")
result = c[["trip_id","fleet_id","trip_fare_pkr","trip_seq","prev_fare","fleet_cum_rev","fare_quartile"]].head(15)
print(result.to_string(index=False))
"""
        out, res = _run_pandas(_code, dfs)
        if out: st.code(out, language="text")
        if isinstance(res, pd.DataFrame): st.dataframe(res, use_container_width=True, height=280, hide_index=True)

# ── TAB 4: STREAMING ─────────────────────────────────────────────────────────
with TAB[4]:
    st.markdown(_h2("Structured Streaming","📡"), unsafe_allow_html=True)
    st.markdown(_card("Spark Structured Streaming treats real-time data as an unbounded DataFrame. Same DataFrame API, adds: output modes, watermarks, triggers, checkpointing.",l=TEAL), unsafe_allow_html=True)
    streaming_concepts = [
        ("Trigger","How often to process new data. Once (batch-like), ProcessingTime('5 minutes') (micro-batch), Continuous (experimental, ms latency).",BRAND),
        ("Output Mode","Append (only new rows), Complete (full updated result), Update (only changed rows since last trigger).",TEAL),
        ("Watermark","Max allowed lateness. withWatermark('event_time','10 minutes') — drops events arriving >10min late.",AMBER),
        ("Checkpoint","Saves streaming state to fault-tolerant storage. Enables recovery from failure. Required for exactly-once.",STEEL),
        ("Stateful ops","Operations that require remembering past events: aggregations, joins, deduplication. State stored in memory.",PUR),
    ]
    c1,c2 = st.columns(2)
    for i,(t,d,c) in enumerate(streaming_concepts):
        (c1 if i%2==0 else c2).markdown(_card(f'<b style="color:{c};font-size:.82rem;">{t}</b><br><span style="font-size:.74rem;color:{TEXT};">{d}</span>',l=c,p="9px 12px"), unsafe_allow_html=True)

    st.code("""from pyspark.sql import functions as F

# Read streaming from Kafka
stream = spark.readStream \\
    .format("kafka") \\
    .option("kafka.bootstrap.servers","kafka:9092") \\
    .option("subscribe","booking-events") \\
    .load()

from pyspark.sql.types import *
schema = StructType([
    StructField("trip_id",StringType()),
    StructField("fleet_id",StringType()),
    StructField("trip_fare_pkr",DoubleType()),
    StructField("pickup_datetime",TimestampType()),
])
events = stream.select(F.from_json(F.col("value").cast("string"),schema).alias("d")).select("d.*")

# Windowed aggregation with watermark
revenue = (events
    .withWatermark("pickup_datetime","10 minutes")
    .groupBy(F.window("pickup_datetime","5 minutes"), F.col("fleet_id"))
    .agg(F.sum("trip_fare_pkr").alias("window_revenue"),
         F.count("trip_id").alias("bookings"))
)

# Write to Delta with checkpointing
query = revenue.writeStream \\
    .format("delta") \\
    .outputMode("append") \\
    .option("checkpointLocation","s3://bucket/checkpoints/booking_revenue/") \\
    .trigger(processingTime="5 minutes") \\
    .start("s3://bucket/streaming/booking_revenue_5min/")

query.awaitTermination()""", language="python")

# ── TAB 5: DELTA LAKE ────────────────────────────────────────────────────────
with TAB[5]:
    st.markdown(_h2("Delta Lake","🔷"), unsafe_allow_html=True)
    delta_features = [
        ("ACID Transactions","Multiple concurrent writes are safe. No corrupt partial writes. Serializable isolation.",BRAND),
        ("Time Travel","Read data at any past point: .option('versionAsOf',5) or .option('timestampAsOf','2026-01-01')",TEAL),
        ("Schema Enforcement","Delta rejects writes with wrong schema. Schema evolution allowed with .option('mergeSchema','true')",AMBER),
        ("Schema Evolution","Add new columns without rewriting old data. Old queries still work.",STEEL),
        ("Upserts (MERGE)","SQL MERGE / Python DeltaTable.merge(). Insert new + update existing in one atomic operation.",PUR),
        ("Optimize & Z-Order","OPTIMIZE: compact small files. Z-ORDER: sort by filter columns for fast multi-dim queries.",ORANGE),
        ("Vacuum","Physically delete old files. VACUUM RETAIN 7 HOURS removes files older than 7hrs retention.",BRAND),
        ("Change Data Feed","Track row-level changes (INSERT/UPDATE/DELETE). Enable streaming from Delta table as CDC source.",TEAL),
    ]
    c1,c2 = st.columns(2)
    for i,(t,d,c) in enumerate(delta_features):
        (c1 if i%2==0 else c2).markdown(_card(f'<b style="color:{c};font-size:.82rem;">{t}</b><br><span style="font-size:.74rem;color:{TEXT};">{d}</span>',l=c,p="9px 12px"), unsafe_allow_html=True)

    st.code("""from delta.tables import DeltaTable

# Write as Delta
trips_df.write.format("delta").mode("overwrite").save("s3://bucket/trips/")

# UPSERT: insert new trips, update fare if changed
dt = DeltaTable.forPath(spark, "s3://bucket/trips/")
dt.alias("target").merge(
    new_trips.alias("source"),
    "target.trip_id = source.trip_id"
).whenMatchedUpdate(set={
    "trip_fare_pkr": "source.trip_fare_pkr",
    "_updated_at": "current_timestamp()",
}).whenNotMatchedInsert(values={"trip_id":"source.trip_id","trip_fare_pkr":"source.trip_fare_pkr"}) \\
  .execute()

# Time travel
trips_v0 = spark.read.format("delta").option("versionAsOf",0).load("s3://bucket/trips/")
trips_yesterday = spark.read.format("delta").option("timestampAsOf","2026-09-25").load("s3://bucket/trips/")

# Optimize + Z-Order for fast fleet+date queries
spark.sql("OPTIMIZE delta.`s3://bucket/trips/` ZORDER BY (fleet_id, pickup_datetime)")
spark.sql("VACUUM delta.`s3://bucket/trips/` RETAIN 168 HOURS")  # 7 days retention""", language="python")

# ── TAB 6: MLLIB ─────────────────────────────────────────────────────────────
with TAB[6]:
    st.markdown(_h2("MLlib — Machine Learning in Spark","🤖"), unsafe_allow_html=True)
    st.code("""from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.regression import GBTRegressor
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.sql import functions as F

trips = spark.read.csv("trips.csv", header=True, inferSchema=True)
completed = trips.filter(F.col("status")=="Completed")

# Feature engineering
fe_df = completed.withColumn("hour", F.hour("pickup_datetime")) \\
    .withColumn("day_of_week", F.dayofweek("pickup_datetime")) \\
    .withColumn("is_weekend", (F.dayofweek("pickup_datetime").isin([1,7])).cast("int")) \\
    .withColumn("is_intercity", (F.col("pickup_city")!=F.col("dropoff_city")).cast("int")) \\
    .withColumn("with_driver_int", F.col("with_driver").cast("int")) \\
    .na.fill(0)

# Encode categorical
indexer = StringIndexer(inputCol="booking_type", outputCol="booking_type_idx")

# Assemble features
assembler = VectorAssembler(
    inputCols=["distance_km","duration_days","hour","day_of_week",
               "is_weekend","is_intercity","with_driver_int","booking_type_idx"],
    outputCol="features"
)

# Model
gbt = GBTRegressor(featuresCol="features", labelCol="trip_fare_pkr", maxIter=50)

# Pipeline
pipeline = Pipeline(stages=[indexer, assembler, gbt])
train, test = fe_df.randomSplit([0.8, 0.2], seed=42)
model = pipeline.fit(train)

# Evaluate
predictions = model.transform(test)
evaluator = RegressionEvaluator(labelCol="trip_fare_pkr", predictionCol="prediction", metricName="rmse")
rmse = evaluator.evaluate(predictions)
print(f"RMSE: PKR {rmse:,.0f}")""", language="python")

    st.markdown(_h3("Pandas + sklearn equivalent (runs here)",TEAL), unsafe_allow_html=True)
    if st.button("▶ Run ML Demo (sklearn)", key="ml_spark"):
        _code = """
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np, pandas as pd

trips = dfs["trips"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"],errors="coerce").fillna(0)
trips["distance_km"]   = pd.to_numeric(trips["distance_km"],  errors="coerce").fillna(0)
trips["duration_days"] = pd.to_numeric(trips["duration_days"],errors="coerce").fillna(0)
trips["pickup_datetime"] = pd.to_datetime(trips["pickup_datetime"],errors="coerce")
c = trips[trips["status"]=="Completed"].copy()
c["hour"]        = c["pickup_datetime"].dt.hour
c["dow"]         = c["pickup_datetime"].dt.dayofweek
c["is_weekend"]  = (c["dow"]>=5).astype(int)
c["is_intercity"]= (c["pickup_city"]!=c["dropoff_city"]).astype(int)
c["with_driver_int"] = pd.to_numeric(c["with_driver"].map({"True":1,"False":0,"true":1,"false":0}),errors="coerce").fillna(0)
feats = ["distance_km","duration_days","hour","dow","is_weekend","is_intercity","with_driver_int"]
X = c[feats].dropna()
y = c.loc[X.index,"trip_fare_pkr"]
X_tr,X_te,y_tr,y_te = train_test_split(X,y,test_size=0.2,random_state=42)
m = GradientBoostingRegressor(n_estimators=50,random_state=42)
m.fit(X_tr,y_tr)
preds = m.predict(X_te)
rmse = np.sqrt(mean_squared_error(y_te,preds))
print(f"RMSE: PKR {rmse:,.0f}")
print(f"R²:   {m.score(X_te,y_te):.3f}")
imp = pd.DataFrame({"Feature":feats,"Importance":m.feature_importances_}).sort_values("Importance",ascending=False)
result = imp
"""
        out, res = _run_pandas(_code, dfs)
        if out: st.code(out, language="text")
        if isinstance(res, pd.DataFrame):
            st.dataframe(res, use_container_width=True, height=200, hide_index=True)

# ── TAB 7: PERFORMANCE ───────────────────────────────────────────────────────
with TAB[7]:
    st.markdown(_h2("Spark Performance Tuning","⚡"), unsafe_allow_html=True)
    perf_tips = [
        ("Avoid collect() on large data","collect() brings ALL data to driver — OOM for large datasets. Use show(), write(), or sample().",BRAND),
        ("Use DataFrame API over RDD","Catalyst optimizer can't optimize RDDs. Always prefer DataFrame/Dataset.",TEAL),
        ("Persist/cache strategically","Use .cache() for DataFrames used in multiple actions. Use .unpersist() when done.",AMBER),
        ("Broadcast small tables","Tables < 10MB: broadcast(df) to avoid expensive shuffle joins.",STEEL),
        ("Repartition before write","df.repartition(200) before write → 200 Parquet files. Aim for 128MB-1GB per file.",PUR),
        ("Coalesce to reduce files","df.coalesce(10) reduces partition count without full shuffle. Use after wide ops.",ORANGE),
        ("Avoid UDFs when possible","Python UDFs break Catalyst optimization. Use built-in F.* functions instead.",BRAND),
        ("Use Parquet over CSV","Parquet: columnar, compressed, predicate pushdown. 10x faster than CSV for analytics.",TEAL),
        ("Tune shuffle partitions","Default 200 partitions. For small data: spark.conf.set('spark.sql.shuffle.partitions','20')",AMBER),
        ("Handle data skew","Salt skewed keys or use broadcast join for highly uneven key distributions.",STEEL),
    ]
    c1,c2 = st.columns(2)
    for i,(t,d,c) in enumerate(perf_tips):
        (c1 if i%2==0 else c2).markdown(_card(f'<b style="color:{c};font-size:.82rem;">{t}</b><br><span style="font-size:.74rem;color:{TEXT};">{d}</span>',l=c,p="9px 12px"), unsafe_allow_html=True)

# ── TAB 8: DATABRICKS ────────────────────────────────────────────────────────
with TAB[8]:
    st.markdown(_h2("Databricks Platform","🏭"), unsafe_allow_html=True)
    st.markdown(_card("Databricks = Managed Apache Spark + Delta Lake + MLflow + Unity Catalog. Runs on AWS, Azure, GCP. The standard enterprise data engineering platform.",l=BRAND), unsafe_allow_html=True)
    db_features = [
        ("Unity Catalog","Centralised governance for all data assets (tables, files, ML models). Fine-grained access control. Cross-workspace sharing.",BRAND),
        ("Delta Live Tables (DLT)","Declarative pipeline framework. Define tables as SQL or Python. Databricks handles orchestration, DQ, monitoring.",TEAL),
        ("Databricks SQL","Serverless SQL warehouse. Run BI queries on Delta Lake. 10-50x faster than Spark for simple SQL.",AMBER),
        ("Auto Loader","Incrementally ingest new files from cloud storage (S3/ADLS). Handles schema evolution automatically.",STEEL),
        ("MLflow","Experiment tracking, model registry, model serving. Integrated into Databricks notebooks.",PUR),
        ("Notebooks","Collaborative notebooks (Python/SQL/R/Scala). Version control via Git. Real-time co-editing.",ORANGE),
        ("Photon Engine","C++ vectorised execution engine. 2-12x faster than Spark for SQL workloads.",TEAL),
        ("Workflows","Orchestration for multi-task jobs. DAG of notebooks/scripts. Retry logic, notifications.",BRAND),
    ]
    c1,c2 = st.columns(2)
    for i,(t,d,c) in enumerate(db_features):
        (c1 if i%2==0 else c2).markdown(_card(f'<b style="color:{c};font-size:.82rem;">{t}</b><br><span style="font-size:.74rem;color:{TEXT};">{d}</span>',l=c,p="9px 12px"), unsafe_allow_html=True)

    st.code("""# Databricks notebook patterns

# 1. Auto Loader: incrementally ingest new files
df = (spark.readStream.format("cloudFiles")
      .option("cloudFiles.format","csv")
      .option("cloudFiles.schemaLocation","dbfs:/mnt/schemas/trips/")
      .load("dbfs:/mnt/raw/trips/"))
df.writeStream.format("delta").trigger(availableNow=True) \\
  .option("checkpointLocation","dbfs:/mnt/checkpoints/trips/") \\
  .toTable("silver.trips")

# 2. Delta Live Tables (DLT) — declarative pipeline
import dlt
@dlt.table(comment="Cleaned trips")
@dlt.expect_all_or_drop({"valid_fare":"trip_fare_pkr > 0","valid_status":"status IS NOT NULL"})
def silver_trips():
    return (spark.table("bronze.raw_trips")
            .filter("trip_id IS NOT NULL")
            .withColumn("trip_fare_pkr", F.col("trip_fare_pkr").cast("double")))

# 3. Unity Catalog governance
spark.sql("GRANT SELECT ON TABLE catalog.schema.trips TO ROLE analyst")
spark.sql("CREATE ROW FILTER policy_fleet ON trips USING (fleet_id = current_user_fleet())")""", language="python")

# ── TAB 9: LIVE LAB (REAL PYSPARK) ──────────────────────────────────────────
with TAB[9]:
    import os as _os, sys as _sys, threading as _threading, subprocess as _subprocess
    from pathlib import Path as _Path

    _CSV_DIR = str(_Path("data/csv").resolve())
    _JAVA_HOME = r"C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot"

    st.markdown(_h2("Live PySpark Lab — Real Spark Execution","💻"), unsafe_allow_html=True)
    st.markdown(_card(
        f'<b style="color:{TEAL};">Real Apache Spark runs locally in your browser.</b><br>'
        f'PySpark 3.5.1 + Java 17 + local[2] mode. Reads real Rent-A-Car CSV data.<br>'
        f'<span style="font-size:.74rem;color:{M};">Note: First run takes ~15s to start JVM. Subsequent runs are faster.</span>',
        l=TEAL, p="10px 14px"), unsafe_allow_html=True)

    # ── Spark runner ──────────────────────────────────────────────────────────
    _SPARK_RUNNER = '''import os, sys, threading
os.environ["JAVA_HOME"] = r"{java_home}"
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
import warnings; warnings.filterwarnings("ignore")

from pyspark.sql import SparkSession, functions as F
from pyspark.sql.window import Window
import pandas as pd

def get_spark():
    return (SparkSession.builder
        .appName("RentACarLab")
        .master("local[2]")
        .config("spark.driver.memory","1g")
        .config("spark.executor.memory","512m")
        .config("spark.sql.shuffle.partitions","4")
        .config("spark.ui.enabled","false")
        .config("spark.driver.extraJavaOptions","-Djava.security.manager=allow")
        .config("spark.sql.execution.arrow.pyspark.enabled","false")
        .getOrCreate())

CSV_DIR = r"{csv_dir}"

# ── USER CODE START ──
{user_code}
# ── USER CODE END ──
'''

    # Pre-built PySpark starters
    _SPARK_STARTERS = {
        "Revenue by fleet (groupBy + SQL)": '''\
spark = get_spark()
spark.sparkContext.setLogLevel("ERROR")

trips = spark.read.csv(f"{CSV_DIR}/trips.csv", header=True, inferSchema=True)
trips.createOrReplaceTempView("trips")

result_df = spark.sql("""
    SELECT fleet_id,
           COUNT(*) AS trips,
           ROUND(SUM(trip_fare_pkr), 0) AS revenue_pkr,
           ROUND(AVG(trip_fare_pkr), 0) AS avg_fare_pkr
    FROM trips
    WHERE status = 'Completed'
    GROUP BY fleet_id
    ORDER BY revenue_pkr DESC
""")
result_df.show()
print(f"Total rows: {trips.count():,}")
spark.stop()''',

        "Window: ROW_NUMBER + running total": '''\
spark = get_spark()
spark.sparkContext.setLogLevel("ERROR")

trips = spark.read.csv(f"{CSV_DIR}/trips.csv", header=True, inferSchema=True)
trips = trips.withColumn("trip_fare_pkr", F.col("trip_fare_pkr").cast("double"))
trips.createOrReplaceTempView("trips")

result_df = spark.sql("""
    SELECT fleet_id, trip_id, trip_fare_pkr,
           ROW_NUMBER() OVER (PARTITION BY fleet_id ORDER BY trip_fare_pkr DESC) AS rank_in_fleet,
           ROUND(SUM(trip_fare_pkr) OVER (
               PARTITION BY fleet_id
               ORDER BY trip_fare_pkr DESC
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
           ), 0) AS cumulative_rev
    FROM trips
    WHERE status = 'Completed'
    QUALIFY rank_in_fleet <= 3
    ORDER BY fleet_id, rank_in_fleet
""")
result_df.show(20)
spark.stop()''',

        "JOIN: trips + customers": '''\
spark = get_spark()
spark.sparkContext.setLogLevel("ERROR")

trips = spark.read.csv(f"{CSV_DIR}/trips.csv", header=True, inferSchema=True)
customers = spark.read.csv(f"{CSV_DIR}/customers.csv", header=True, inferSchema=True)
trips.createOrReplaceTempView("trips")
customers.createOrReplaceTempView("customers")

result_df = spark.sql("""
    SELECT c.full_name, c.city, c.customer_type,
           COUNT(t.trip_id) AS total_trips,
           ROUND(SUM(t.trip_fare_pkr), 0) AS total_spend_pkr
    FROM trips t
    JOIN customers c ON t.customer_id = c.customer_id
    WHERE t.status = 'Completed'
    GROUP BY c.full_name, c.city, c.customer_type
    ORDER BY total_spend_pkr DESC
    LIMIT 10
""")
result_df.show()
spark.stop()''',

        "Aggregation: ROLLUP with subtotals": '''\
spark = get_spark()
spark.sparkContext.setLogLevel("ERROR")

trips = spark.read.csv(f"{CSV_DIR}/trips.csv", header=True, inferSchema=True)
trips.createOrReplaceTempView("trips")

result_df = spark.sql("""
    SELECT COALESCE(fleet_id, 'ALL FLEETS') AS fleet,
           COALESCE(booking_type, 'ALL TYPES') AS booking_type,
           COUNT(*) AS trips,
           ROUND(SUM(trip_fare_pkr), 0) AS revenue_pkr
    FROM trips
    WHERE status = 'Completed'
    GROUP BY ROLLUP(fleet_id, booking_type)
    ORDER BY fleet NULLS LAST, booking_type NULLS LAST
""")
result_df.show(30)
spark.stop()''',

        "Month-over-month LAG": '''\
spark = get_spark()
spark.sparkContext.setLogLevel("ERROR")

trips = spark.read.csv(f"{CSV_DIR}/trips.csv", header=True, inferSchema=True)
trips.createOrReplaceTempView("trips")

result_df = spark.sql("""
    WITH monthly AS (
        SELECT DATE_TRUNC('month', pickup_datetime) AS month,
               SUM(trip_fare_pkr) AS revenue
        FROM trips WHERE status = 'Completed'
        GROUP BY 1
    )
    SELECT month,
           ROUND(revenue, 0) AS revenue_pkr,
           ROUND(LAG(revenue) OVER (ORDER BY month), 0) AS prev_month,
           ROUND((revenue - LAG(revenue) OVER (ORDER BY month)) * 100.0
                 / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 1) AS mom_pct
    FROM monthly
    ORDER BY month DESC
    LIMIT 12
""")
result_df.show()
spark.stop()''',

        "QUALIFY: top vehicle per fleet": '''\
spark = get_spark()
spark.sparkContext.setLogLevel("ERROR")

trips = spark.read.csv(f"{CSV_DIR}/trips.csv", header=True, inferSchema=True)
trips.createOrReplaceTempView("trips")

result_df = spark.sql("""
    SELECT fleet_id, vehicle_id,
           ROUND(SUM(trip_fare_pkr), 0) AS revenue_pkr,
           COUNT(*) AS trips,
           ROW_NUMBER() OVER (PARTITION BY fleet_id ORDER BY SUM(trip_fare_pkr) DESC) AS rn
    FROM trips
    WHERE status = 'Completed'
    GROUP BY fleet_id, vehicle_id
    QUALIFY rn = 1
    ORDER BY revenue_pkr DESC
""")
result_df.show()
spark.stop()''',

        "DQ check: find bad data": '''\
spark = get_spark()
spark.sparkContext.setLogLevel("ERROR")

trips = spark.read.csv(f"{CSV_DIR}/trips.csv", header=True, inferSchema=True)
trips.createOrReplaceTempView("trips")

# Timeline violations
spark.sql("""
    SELECT trip_id, pickup_datetime, dropoff_datetime,
           DATEDIFF(CAST(dropoff_datetime AS TIMESTAMP),
                    CAST(pickup_datetime AS TIMESTAMP)) AS dur_days
    FROM trips
    WHERE CAST(dropoff_datetime AS TIMESTAMP) < CAST(pickup_datetime AS TIMESTAMP)
    LIMIT 10
""").show()

# Null / zero fare
result_df = spark.sql("""
    SELECT
        COUNT(*) AS total,
        SUM(CASE WHEN customer_id IS NULL OR customer_id='' THEN 1 ELSE 0 END) AS null_customer,
        SUM(CASE WHEN CAST(trip_fare_pkr AS DOUBLE) <= 0 THEN 1 ELSE 0 END) AS zero_fare,
        ROUND(SUM(CASE WHEN CAST(trip_fare_pkr AS DOUBLE) <= 0 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS pct_bad_fare
    FROM trips
""")
result_df.show()
spark.stop()''',

        "Multi-table join: P&L by fleet": '''\
spark = get_spark()
spark.sparkContext.setLogLevel("ERROR")

for tbl in ["trips","fuel_logs","maintenance","fleets"]:
    df = spark.read.csv(f"{CSV_DIR}/{tbl}.csv", header=True, inferSchema=True)
    df.createOrReplaceTempView(tbl)

result_df = spark.sql("""
    SELECT f.fleet_name,
           COUNT(t.trip_id) AS trips,
           ROUND(SUM(t.trip_fare_pkr), 0) AS revenue_pkr,
           ROUND(SUM(fl.fuel_cost_pkr), 0) AS fuel_cost,
           ROUND(SUM(m.total_cost_pkr), 0) AS maint_cost,
           ROUND(SUM(t.trip_fare_pkr) - COALESCE(SUM(fl.fuel_cost_pkr),0)
                 - COALESCE(SUM(m.total_cost_pkr),0), 0) AS gross_profit
    FROM trips t
    JOIN fleets f ON t.fleet_id = f.fleet_id
    LEFT JOIN (SELECT fleet_id, SUM(fuel_cost_pkr) AS fuel_cost_pkr FROM fuel_logs GROUP BY 1) fl
           ON t.fleet_id = fl.fleet_id
    LEFT JOIN (SELECT fleet_id, SUM(total_cost_pkr) AS total_cost_pkr FROM maintenance GROUP BY 1) m
           ON t.fleet_id = m.fleet_id
    WHERE t.status = 'Completed'
    GROUP BY f.fleet_name
    ORDER BY gross_profit DESC
""")
result_df.show()
spark.stop()''',
    }

    # ── UI Layout ─────────────────────────────────────────────────────────────
    _sel_col, _mode_col = st.columns([2, 1])
    with _sel_col:
        _spark_sel = st.selectbox("Load example:", list(_SPARK_STARTERS.keys()), key="spark_sel")
    with _mode_col:
        _run_mode = st.radio("Run mode:", ["🔥 Real PySpark","🐼 pandas fallback"], key="spark_mode", horizontal=True)

    if "spark_lab_code" not in st.session_state:
        st.session_state["spark_lab_code"] = _SPARK_STARTERS[_spark_sel]

    if st.button("📋 Load Example", key="load_spark_ex", use_container_width=False):
        st.session_state["spark_lab_ace"] = _SPARK_STARTERS[_spark_sel]
        st.session_state["spark_lab_code"] = _SPARK_STARTERS[_spark_sel]
        st.rerun()

    from streamlit_ace import st_ace as _ace_spark
    _spark_code = _ace_spark(
        value=st.session_state.get("spark_lab_ace", st.session_state["spark_lab_code"]),
        language="python", theme="monokai",
        key="spark_ace_main", height=320,
        font_size=14, tab_size=4,
        show_gutter=True, auto_update=True,
        placeholder="# Write PySpark SQL here...",
    )
    if _spark_code:
        st.session_state["spark_lab_ace"] = _spark_code
        st.session_state["spark_lab_code"] = _spark_code

    _run_btn = st.button("▶ Run PySpark", type="primary", key="run_spark_real", use_container_width=False)

    if _run_btn:
        _code = st.session_state["spark_lab_code"]
        if "Real PySpark" in _run_mode:
            # ── Real PySpark execution via subprocess ─────────────────────────
            _full_script = (_SPARK_RUNNER
                .replace("{java_home}", _JAVA_HOME)
                .replace("{csv_dir}", _CSV_DIR.replace("\\","\\\\"))
                .replace("{user_code}", _code))

            _script_path = _Path("data/_spark_runner_temp.py")
            _script_path.write_text(_full_script, encoding="utf-8")

            st.markdown(
                f'<div style="background:#161b22;border:1px solid #30363d;border-radius:8px 8px 0 0;'
                f'padding:6px 14px;font-size:.72rem;color:#8b949e;display:flex;align-items:center;gap:8px;">'
                f'<span style="width:11px;height:11px;border-radius:50%;background:#ff5f57;display:inline-block;"></span>'
                f'<span style="width:11px;height:11px;border-radius:50%;background:#febc2e;display:inline-block;"></span>'
                f'<span style="width:11px;height:11px;border-radius:50%;background:#28c840;display:inline-block;"></span>'
                f'&nbsp; PySpark 3.5.1 · local[2] · Java 17</div>',
                unsafe_allow_html=True,
            )
            _term = st.empty()
            _prog = st.progress(0, text="Starting JVM…")

            _env = {
                **_os.environ,
                "JAVA_HOME": _JAVA_HOME,
                "PYSPARK_PYTHON": _sys.executable,
                "PYSPARK_DRIVER_PYTHON": _sys.executable,
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
            }
            _lines: list[str] = ["$ pyspark --master local[2]", ""]

            def _render_term(lines):
                def _c(l):
                    if "ERROR" in l or "Exception" in l: return f'<span style="color:#f85149;">{l}</span>'
                    if "+--" in l or "|" in l: return f'<span style="color:#3fb950;">{l}</span>'
                    if "WARN" in l: return f'<span style="color:#e3b341;">{l}</span>'
                    if l.startswith("$"): return f'<span style="color:#e63946;font-weight:700;">{l}</span>'
                    return f'<span style="color:#8b949e;">{l}</span>'
                body = "\n".join(_c(ln) for ln in lines[-60:])
                _term.markdown(f'<div style="background:#0d1117;border:1px solid #30363d;border-radius:0 0 8px 8px;padding:14px 16px;font-family:monospace;font-size:.75rem;line-height:1.7;max-height:420px;overflow-y:auto;white-space:pre-wrap;">{body}</div>', unsafe_allow_html=True)

            _render_term(_lines)

            try:
                _proc = _subprocess.Popen(
                    [_sys.executable, str(_script_path)],
                    stdout=_subprocess.PIPE,
                    stderr=_subprocess.STDOUT,
                    text=True, bufsize=1,
                    encoding="utf-8", errors="replace",
                    env=_env,
                )
                _progress_val = 10
                for _raw in _proc.stdout:
                    _ln = _raw.rstrip()
                    if not _ln:
                        continue
                    # Skip JVM internal noise but KEEP query results (lines with +-- or |)
                    _is_table = _ln.startswith("|") or _ln.startswith("+")
                    _is_result = "PYSPARK_OK" in _ln or _is_table
                    _is_noise = (
                        ("INFO" in _ln and not _is_result) or
                        ("log4j" in _ln.lower() and not _is_result) or
                        ("ShutdownHookManager" in _ln) or
                        ("NoSuchFileException" in _ln) or
                        ("WindowsException" in _ln) or
                        ("at java.base" in _ln) or
                        ("at org.apache.spark" in _ln) or
                        ("at scala." in _ln)
                    )
                    if _is_noise:
                        continue
                    _lines.append(_ln)
                    if _progress_val < 90: _progress_val += 3
                    _prog.progress(_progress_val, text="Running…")
                    _render_term(_lines)

                _proc.wait()
                _prog.progress(100, text="✅ Done!")
                _lines.append(f"\n✅ Spark job finished (exit {_proc.returncode})")
                _render_term(_lines)

            except Exception as _ex:
                _lines.append(f"❌ Error: {_ex}")
                _render_term(_lines)
            finally:
                try: _script_path.unlink()
                except: pass

        else:
            # ── pandas fallback ───────────────────────────────────────────────
            st.info("Running as pandas (no Spark JVM)…")
            import io as _io2, contextlib as _cl2
            _buf = _io2.StringIO()
            _ns  = {"dfs":dfs,"pd":pd,"np":np,"result":None}
            _pandas_code = _code
            for _tbl in ["trips","customers","vehicles","fleets","drivers","fuel_logs","maintenance"]:
                _pandas_code = _pandas_code.replace(
                    f'spark.read.csv(f"{{CSV_DIR}}/{_tbl}.csv", header=True, inferSchema=True)',
                    f'_spark_compat_df(dfs, "{_tbl}")')
            _ns["_spark_compat_df"] = lambda dfs, t: dfs.get(t, pd.DataFrame())
            with _cl2.redirect_stdout(_buf):
                try: exec(compile(_pandas_code,"<pandas>","exec"),_ns)
                except Exception as e: print(f"Error: {e}")
            if _buf.getvalue(): st.code(_buf.getvalue(), language="text")
            if isinstance(_ns.get("result"), pd.DataFrame):
                st.dataframe(_ns["result"], use_container_width=True, height=280, hide_index=True)

    # ── Schema reference ─────────────────────────────────────────────────────
    with st.expander("📋 Available CSV tables & columns", expanded=False):
        _schema = {
            "trips":      "trip_id, fleet_id, vehicle_id, driver_id, customer_id, booking_type, pickup_datetime, dropoff_datetime, pickup_city, dropoff_city, distance_km, trip_fare_pkr, status",
            "customers":  "customer_id, full_name, gender, email, phone, city, customer_type, loyalty_points, registration_date",
            "vehicles":   "vehicle_id, fleet_id, make, model, year, fuel_type, odometer_km, daily_rate_pkr, status",
            "drivers":    "driver_id, fleet_id, full_name, experience_years, ratings_avg, behavior_profile, active",
            "fleets":     "fleet_id, fleet_name, city, established_year, focus_segment",
            "invoices":   "invoice_id, trip_id, customer_id, fleet_id, total_amount_pkr, paid_amount_pkr, payment_status",
            "fuel_logs":  "fuel_id, trip_id, vehicle_id, fleet_id, fill_date, litres_filled, fuel_cost_pkr, fuel_efficiency_kmpl",
            "maintenance":"maint_id, vehicle_id, fleet_id, maintenance_type, total_cost_pkr, maintenance_date",
            "telematics": "telem_id, trip_id, driver_id, vehicle_id, safety_score, customer_rating, accident_occurred",
        }
        st.markdown(f'<div style="font-size:.72rem;color:{M};">Load with: <code>df = spark.read.csv(f"{{CSV_DIR}}/trips.csv", header=True, inferSchema=True)</code></div>', unsafe_allow_html=True)
        for _t, _c in _schema.items():
            st.markdown(f'<div style="font-family:monospace;font-size:.72rem;margin:2px 0;"><span style="color:{BRAND};">{_t}</span><span style="color:{M};"> — {_c}</span></div>', unsafe_allow_html=True)

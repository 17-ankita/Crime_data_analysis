<<<<<<< HEAD
"""
=============================================================
  CRIME DATA ANALYTICS — SQL LAYER
  Creates SQLite DB from Excel, runs 15 analytical queries
=============================================================
"""

import sqlite3
import pandas as pd

# ── 1. Load & ingest ─────────────────────────────────────────
df = pd.read_excel("crime_data.xlsx")
df.columns = [c.strip().replace(" ", "_").replace("(", "").replace(")", "").replace("?", "").replace("/", "_") for c in df.columns]

conn = sqlite3.connect("crime_analytics.db")
df.to_sql("crimes", conn, if_exists="replace", index=False)
print("✓ Database created — crimes table loaded with", len(df), "rows\n")

def run(title, sql):
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)
    result = pd.read_sql_query(sql, conn)
    print(result.to_string(index=False))
    print()

# ── 2. SQL Queries ────────────────────────────────────────────

run("Q1 — Total crimes per year (trend)","""
SELECT Year,
       COUNT(*)                          AS total_crimes,
       ROUND(COUNT(*) * 100.0 / 200, 1) AS pct_share
FROM   crimes
GROUP  BY Year
ORDER  BY Year;
""")

run("Q2 — Top 5 cities by crime count & avg property loss","""
SELECT City,
       COUNT(*)                             AS total_cases,
       ROUND(AVG("Property_Loss_INR"), 0)   AS avg_loss_inr,
       ROUND(AVG(Police_Response_Time_mins),1) AS avg_response_min
FROM   crimes
GROUP  BY City
ORDER  BY total_cases DESC
LIMIT  5;
""")

run("Q3 — Crime type breakdown with conviction rate","""
SELECT Crime_Type,
       COUNT(*)                                           AS total,
       SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END) AS convictions,
       ROUND(SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS conviction_rate_pct,
       ROUND(AVG(Days_to_Resolve),1)                     AS avg_days_to_resolve
FROM   crimes
GROUP  BY Crime_Type
ORDER  BY conviction_rate_pct DESC;
""")

run("Q4 — Severity distribution per crime type","""
SELECT Crime_Type,
       SUM(CASE WHEN Severity='Critical' THEN 1 ELSE 0 END) AS Critical,
       SUM(CASE WHEN Severity='High'     THEN 1 ELSE 0 END) AS High,
       SUM(CASE WHEN Severity='Medium'   THEN 1 ELSE 0 END) AS Medium,
       SUM(CASE WHEN Severity='Low'      THEN 1 ELSE 0 END) AS Low
FROM   crimes
GROUP  BY Crime_Type
ORDER  BY Crime_Type;
""")

run("Q5 — Time-of-day crime hotspots","""
SELECT Time_of_Day,
       COUNT(*)                           AS crimes,
       ROUND(COUNT(*)*100.0/200,1)        AS pct,
       ROUND(AVG(Police_Response_Time_mins),1) AS avg_response_min,
       SUM(Casualties)                    AS total_casualties,
       SUM(Injuries)                      AS total_injuries
FROM   crimes
GROUP  BY Time_of_Day
ORDER  BY crimes DESC;
""")

run("Q6 — Seasonal & day-type patterns","""
SELECT Season,
       Day_Type,
       COUNT(*) AS crimes,
       ROUND(AVG("Property_Loss_INR"),0) AS avg_property_loss
FROM   crimes
GROUP  BY Season, Day_Type
ORDER  BY Season, crimes DESC;
""")

run("Q7 — Weapon type impact on casualties","""
SELECT Weapon_Type,
       COUNT(*)                              AS cases,
       SUM(Casualties)                       AS total_casualties,
       SUM(Injuries)                         AS total_injuries,
       ROUND(AVG(Casualties),2)              AS avg_casualties,
       ROUND(AVG(Police_Response_Time_mins),1) AS avg_response_min
FROM   crimes
GROUP  BY Weapon_Type
ORDER  BY total_casualties DESC;
""")

run("Q8 — Case status pipeline","""
SELECT Case_Status,
       COUNT(*)                                            AS count,
       ROUND(COUNT(*)*100.0/200,1)                        AS pct,
       ROUND(AVG(Days_to_Resolve),1)                      AS avg_days,
       SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END)  AS convictions
FROM   crimes
GROUP  BY Case_Status
ORDER  BY count DESC;
""")

run("Q9 — CCTV & witness effect on conviction","""
SELECT CCTV_Available,
       Witness_Present,
       COUNT(*)                                                         AS cases,
       SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END)               AS conv,
       ROUND(SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS conv_rate_pct
FROM   crimes
GROUP  BY CCTV_Available, Witness_Present
ORDER  BY conv_rate_pct DESC;
""")

run("Q10 — Repeat offender analysis","""
SELECT Repeat_Offender,
       COUNT(*)                                                          AS cases,
       ROUND(AVG(Days_to_Resolve),1)                                    AS avg_days_resolve,
       SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END)                AS convictions,
       ROUND(SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS conv_rate_pct,
       ROUND(AVG("Property_Loss_INR"),0)                                AS avg_loss_inr
FROM   crimes
GROUP  BY Repeat_Offender;
""")

run("Q11 — Location type risk ranking","""
SELECT Location_Type,
       COUNT(*)                              AS total_crimes,
       ROUND(AVG(Number_of_Victims),2)       AS avg_victims,
       SUM(Casualties)                        AS total_casualties,
       ROUND(AVG("Property_Loss_INR"),0)     AS avg_loss_inr,
       ROUND(AVG(Officers_Assigned),1)       AS avg_officers
FROM   crimes
GROUP  BY Location_Type
ORDER  BY total_crimes DESC;
""")

run("Q12 — Victim age group breakdown by crime type (pivot)","""
SELECT Crime_Type,
       SUM(CASE WHEN Victim_Age_Group='<18'   THEN 1 ELSE 0 END) AS under_18,
       SUM(CASE WHEN Victim_Age_Group='18-30' THEN 1 ELSE 0 END) AS age_18_30,
       SUM(CASE WHEN Victim_Age_Group='31-45' THEN 1 ELSE 0 END) AS age_31_45,
       SUM(CASE WHEN Victim_Age_Group='46-60' THEN 1 ELSE 0 END) AS age_46_60,
       SUM(CASE WHEN Victim_Age_Group='60+'   THEN 1 ELSE 0 END) AS age_60_plus,
       SUM(CASE WHEN Victim_Age_Group='Unknown' THEN 1 ELSE 0 END) AS unknown
FROM   crimes
GROUP  BY Crime_Type
ORDER  BY Crime_Type;
""")

run("Q13 — Police response time SLA buckets","""
SELECT CASE
         WHEN Police_Response_Time_mins <= 15 THEN '0-15 min (Excellent)'
         WHEN Police_Response_Time_mins <= 30 THEN '16-30 min (Good)'
         WHEN Police_Response_Time_mins <= 60 THEN '31-60 min (Average)'
         WHEN Police_Response_Time_mins <= 90 THEN '61-90 min (Slow)'
         ELSE '90+ min (Critical)'
       END AS response_sla,
       COUNT(*) AS cases,
       ROUND(COUNT(*)*100.0/200,1) AS pct
FROM   crimes
GROUP  BY response_sla
ORDER  BY MIN(Police_Response_Time_mins);
""")

run("Q14 — High-value property loss crimes (top 10)","""
SELECT FIR_Number, City, Crime_Type, Severity,
       ROUND("Property_Loss_INR",0) AS property_loss_inr,
       Case_Status, Conviction
FROM   crimes
WHERE  "Property_Loss_INR" > 0
ORDER  BY "Property_Loss_INR" DESC
LIMIT  10;
""")

run("Q15 — City-level scorecard (composite)","""
SELECT City,
       COUNT(*)                                                           AS total_cases,
       ROUND(AVG(Police_Response_Time_mins),1)                           AS avg_response_min,
       ROUND(SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS conv_rate_pct,
       ROUND(AVG("Property_Loss_INR"),0)                                 AS avg_loss_inr,
       SUM(Casualties)                                                    AS total_casualties,
       ROUND(AVG(Days_to_Resolve),0)                                     AS avg_days_resolve
FROM   crimes
GROUP  BY City
ORDER  BY total_cases DESC;
""")

conn.close()
print("✓ All SQL queries complete.")
=======
"""
=============================================================
  CRIME DATA ANALYTICS — SQL LAYER
  Creates SQLite DB from Excel, runs 15 analytical queries
=============================================================
"""

import sqlite3
import pandas as pd

# ── 1. Load & ingest ─────────────────────────────────────────
df = pd.read_excel("crime_data.xlsx")
df.columns = [c.strip().replace(" ", "_").replace("(", "").replace(")", "").replace("?", "").replace("/", "_") for c in df.columns]

conn = sqlite3.connect("crime_analytics.db")
df.to_sql("crimes", conn, if_exists="replace", index=False)
print("✓ Database created — crimes table loaded with", len(df), "rows\n")

def run(title, sql):
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)
    result = pd.read_sql_query(sql, conn)
    print(result.to_string(index=False))
    print()

# ── 2. SQL Queries ────────────────────────────────────────────

run("Q1 — Total crimes per year (trend)","""
SELECT Year,
       COUNT(*)                          AS total_crimes,
       ROUND(COUNT(*) * 100.0 / 200, 1) AS pct_share
FROM   crimes
GROUP  BY Year
ORDER  BY Year;
""")

run("Q2 — Top 5 cities by crime count & avg property loss","""
SELECT City,
       COUNT(*)                             AS total_cases,
       ROUND(AVG("Property_Loss_INR"), 0)   AS avg_loss_inr,
       ROUND(AVG(Police_Response_Time_mins),1) AS avg_response_min
FROM   crimes
GROUP  BY City
ORDER  BY total_cases DESC
LIMIT  5;
""")

run("Q3 — Crime type breakdown with conviction rate","""
SELECT Crime_Type,
       COUNT(*)                                           AS total,
       SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END) AS convictions,
       ROUND(SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS conviction_rate_pct,
       ROUND(AVG(Days_to_Resolve),1)                     AS avg_days_to_resolve
FROM   crimes
GROUP  BY Crime_Type
ORDER  BY conviction_rate_pct DESC;
""")

run("Q4 — Severity distribution per crime type","""
SELECT Crime_Type,
       SUM(CASE WHEN Severity='Critical' THEN 1 ELSE 0 END) AS Critical,
       SUM(CASE WHEN Severity='High'     THEN 1 ELSE 0 END) AS High,
       SUM(CASE WHEN Severity='Medium'   THEN 1 ELSE 0 END) AS Medium,
       SUM(CASE WHEN Severity='Low'      THEN 1 ELSE 0 END) AS Low
FROM   crimes
GROUP  BY Crime_Type
ORDER  BY Crime_Type;
""")

run("Q5 — Time-of-day crime hotspots","""
SELECT Time_of_Day,
       COUNT(*)                           AS crimes,
       ROUND(COUNT(*)*100.0/200,1)        AS pct,
       ROUND(AVG(Police_Response_Time_mins),1) AS avg_response_min,
       SUM(Casualties)                    AS total_casualties,
       SUM(Injuries)                      AS total_injuries
FROM   crimes
GROUP  BY Time_of_Day
ORDER  BY crimes DESC;
""")

run("Q6 — Seasonal & day-type patterns","""
SELECT Season,
       Day_Type,
       COUNT(*) AS crimes,
       ROUND(AVG("Property_Loss_INR"),0) AS avg_property_loss
FROM   crimes
GROUP  BY Season, Day_Type
ORDER  BY Season, crimes DESC;
""")

run("Q7 — Weapon type impact on casualties","""
SELECT Weapon_Type,
       COUNT(*)                              AS cases,
       SUM(Casualties)                       AS total_casualties,
       SUM(Injuries)                         AS total_injuries,
       ROUND(AVG(Casualties),2)              AS avg_casualties,
       ROUND(AVG(Police_Response_Time_mins),1) AS avg_response_min
FROM   crimes
GROUP  BY Weapon_Type
ORDER  BY total_casualties DESC;
""")

run("Q8 — Case status pipeline","""
SELECT Case_Status,
       COUNT(*)                                            AS count,
       ROUND(COUNT(*)*100.0/200,1)                        AS pct,
       ROUND(AVG(Days_to_Resolve),1)                      AS avg_days,
       SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END)  AS convictions
FROM   crimes
GROUP  BY Case_Status
ORDER  BY count DESC;
""")

run("Q9 — CCTV & witness effect on conviction","""
SELECT CCTV_Available,
       Witness_Present,
       COUNT(*)                                                         AS cases,
       SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END)               AS conv,
       ROUND(SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS conv_rate_pct
FROM   crimes
GROUP  BY CCTV_Available, Witness_Present
ORDER  BY conv_rate_pct DESC;
""")

run("Q10 — Repeat offender analysis","""
SELECT Repeat_Offender,
       COUNT(*)                                                          AS cases,
       ROUND(AVG(Days_to_Resolve),1)                                    AS avg_days_resolve,
       SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END)                AS convictions,
       ROUND(SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS conv_rate_pct,
       ROUND(AVG("Property_Loss_INR"),0)                                AS avg_loss_inr
FROM   crimes
GROUP  BY Repeat_Offender;
""")

run("Q11 — Location type risk ranking","""
SELECT Location_Type,
       COUNT(*)                              AS total_crimes,
       ROUND(AVG(Number_of_Victims),2)       AS avg_victims,
       SUM(Casualties)                        AS total_casualties,
       ROUND(AVG("Property_Loss_INR"),0)     AS avg_loss_inr,
       ROUND(AVG(Officers_Assigned),1)       AS avg_officers
FROM   crimes
GROUP  BY Location_Type
ORDER  BY total_crimes DESC;
""")

run("Q12 — Victim age group breakdown by crime type (pivot)","""
SELECT Crime_Type,
       SUM(CASE WHEN Victim_Age_Group='<18'   THEN 1 ELSE 0 END) AS under_18,
       SUM(CASE WHEN Victim_Age_Group='18-30' THEN 1 ELSE 0 END) AS age_18_30,
       SUM(CASE WHEN Victim_Age_Group='31-45' THEN 1 ELSE 0 END) AS age_31_45,
       SUM(CASE WHEN Victim_Age_Group='46-60' THEN 1 ELSE 0 END) AS age_46_60,
       SUM(CASE WHEN Victim_Age_Group='60+'   THEN 1 ELSE 0 END) AS age_60_plus,
       SUM(CASE WHEN Victim_Age_Group='Unknown' THEN 1 ELSE 0 END) AS unknown
FROM   crimes
GROUP  BY Crime_Type
ORDER  BY Crime_Type;
""")

run("Q13 — Police response time SLA buckets","""
SELECT CASE
         WHEN Police_Response_Time_mins <= 15 THEN '0-15 min (Excellent)'
         WHEN Police_Response_Time_mins <= 30 THEN '16-30 min (Good)'
         WHEN Police_Response_Time_mins <= 60 THEN '31-60 min (Average)'
         WHEN Police_Response_Time_mins <= 90 THEN '61-90 min (Slow)'
         ELSE '90+ min (Critical)'
       END AS response_sla,
       COUNT(*) AS cases,
       ROUND(COUNT(*)*100.0/200,1) AS pct
FROM   crimes
GROUP  BY response_sla
ORDER  BY MIN(Police_Response_Time_mins);
""")

run("Q14 — High-value property loss crimes (top 10)","""
SELECT FIR_Number, City, Crime_Type, Severity,
       ROUND("Property_Loss_INR",0) AS property_loss_inr,
       Case_Status, Conviction
FROM   crimes
WHERE  "Property_Loss_INR" > 0
ORDER  BY "Property_Loss_INR" DESC
LIMIT  10;
""")

run("Q15 — City-level scorecard (composite)","""
SELECT City,
       COUNT(*)                                                           AS total_cases,
       ROUND(AVG(Police_Response_Time_mins),1)                           AS avg_response_min,
       ROUND(SUM(CASE WHEN Conviction='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS conv_rate_pct,
       ROUND(AVG("Property_Loss_INR"),0)                                 AS avg_loss_inr,
       SUM(Casualties)                                                    AS total_casualties,
       ROUND(AVG(Days_to_Resolve),0)                                     AS avg_days_resolve
FROM   crimes
GROUP  BY City
ORDER  BY total_cases DESC;
""")

conn.close()
print("✓ All SQL queries complete.")
>>>>>>> 640c70f3fdd4027bf2402a64d8c57b82eb9a02de

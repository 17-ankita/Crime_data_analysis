<<<<<<< HEAD
"""
=============================================================
  CRIME DATA ANALYTICS — PYTHON EDA + ML
  - Exploratory Data Analysis
  - Feature Engineering
  - ML: Conviction Predictor (Random Forest)
  - ML: Crime Severity Classifier
  - ML: Days-to-Resolve Regressor
=============================================================
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, confusion_matrix,
                             mean_absolute_error, r2_score, accuracy_score)
from sklearn.preprocessing import StandardScaler

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "font.size":        11,
    "axes.titlesize":   13,
    "axes.titleweight": "bold",
})
PALETTE = ["#378ADD","#7F77DD","#1D9E75","#D85A30","#BA7517","#A32D2D","#639922"]

# ── 1. Load & inspect ─────────────────────────────────────────
print("=" * 60)
print("  1. DATA LOADING & BASIC INSPECTION")
print("=" * 60)

df = pd.read_excel("crime_data.xlsx")
print(f"Shape         : {df.shape}")
print(f"Columns       : {list(df.columns)}")
print(f"\nData types:\n{df.dtypes.to_string()}")
print(f"\nNull values:\n{df.isnull().sum().to_string()}")
print(f"\nDescriptive stats (numeric):")
print(df.describe().round(2).to_string())

# ── 2. Feature Engineering ─────────────────────────────────────
print("\n" + "=" * 60)
print("  2. FEATURE ENGINEERING")
print("=" * 60)

df["Date of Crime"] = pd.to_datetime(df["Date of Crime"])
df["crime_month_num"]  = df["Date of Crime"].dt.month
df["high_value_loss"]  = (df["Property Loss (INR)"] > df["Property Loss (INR)"].median()).astype(int)
df["fast_response"]    = (df["Police Response Time (mins)"] <= 30).astype(int)
df["multi_victim"]     = (df["Number of Victims"] > 2).astype(int)
df["severity_score"]   = df["Severity"].map({"Low":1,"Medium":2,"High":3,"Critical":4})
df["conviction_bin"]   = (df["Conviction"] == "Yes").astype(int)
df["cctv_witness"]     = ((df["CCTV Available"]=="Yes") & (df["Witness Present"]=="Yes")).astype(int)

print("New features added:")
new_feats = ["crime_month_num","high_value_loss","fast_response",
             "multi_victim","severity_score","conviction_bin","cctv_witness"]
print(df[new_feats].describe().round(2).to_string())

# ── 3. EDA Plots ───────────────────────────────────────────────
print("\n" + "=" * 60)
print("  3. EXPLORATORY DATA ANALYSIS — generating plots …")
print("=" * 60)

# ---- Figure 1: Crime overview (2×3) --------------------------
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle("Crime Data — Exploratory Analysis", fontsize=16, fontweight="bold", y=1.01)

# 3a. Crime type bar
ct = df["Crime Type"].value_counts()
axes[0,0].barh(ct.index, ct.values, color=PALETTE[0])
axes[0,0].set_title("Crime type distribution")
axes[0,0].set_xlabel("Count")
for i, v in enumerate(ct.values):
    axes[0,0].text(v+0.2, i, str(v), va="center", fontsize=9)

# 3b. Year trend
yr = df["Year"].value_counts().sort_index()
axes[0,1].plot(yr.index, yr.values, marker="o", color=PALETTE[1], linewidth=2.5, markersize=8)
axes[0,1].fill_between(yr.index, yr.values, alpha=0.15, color=PALETTE[1])
axes[0,1].set_title("Annual crime trend")
axes[0,1].set_xlabel("Year"); axes[0,1].set_ylabel("Cases")

# 3c. Property loss distribution
axes[0,2].hist(df[df["Property Loss (INR)"]>0]["Property Loss (INR)"],
               bins=20, color=PALETTE[2], edgecolor="white")
axes[0,2].set_title("Property loss distribution (INR)")
axes[0,2].set_xlabel("Loss (INR)"); axes[0,2].set_ylabel("Frequency")

# 3d. Response time by city (boxplot)
city_order = df.groupby("City")["Police Response Time (mins)"].median().sort_values().index
sns.boxplot(data=df, y="City", x="Police Response Time (mins)",
            order=city_order, ax=axes[1,0], palette="Blues_r")
axes[1,0].set_title("Police response time by city")

# 3e. Conviction rate by crime type
conv = df.groupby("Crime Type")["conviction_bin"].mean().sort_values()
bars = axes[1,1].barh(conv.index, conv.values * 100,
                      color=[PALETTE[2] if v>=0.6 else PALETTE[4] if v>=0.5 else PALETTE[5]
                             for v in conv.values])
axes[1,1].set_title("Conviction rate by crime type (%)")
axes[1,1].set_xlabel("Conviction rate %")
axes[1,1].axvline(x=57, color="gray", linestyle="--", alpha=0.7, label="Overall avg")
axes[1,1].legend(fontsize=9)

# 3f. Severity × Season heatmap
pivot = df.groupby(["Season","Severity"]).size().unstack(fill_value=0)
pivot = pivot[["Low","Medium","High","Critical"]]
sns.heatmap(pivot, annot=True, fmt="d", cmap="YlOrRd", ax=axes[1,2], linewidths=0.5)
axes[1,2].set_title("Crime count: Season × Severity")

plt.tight_layout()
plt.savefig("eda_overview.png", dpi=130, bbox_inches="tight")
plt.close()
print("  ✓ eda_overview.png saved")

# ---- Figure 2: Deep-dive correlations & patterns -------------
fig2, axes2 = plt.subplots(2, 3, figsize=(18, 10))
fig2.suptitle("Crime Data — Deep-Dive Analysis", fontsize=16, fontweight="bold")

# 4a. Time of day × crime type heatmap
tod_ct = df.groupby(["Time of Day","Crime Type"]).size().unstack(fill_value=0)
sns.heatmap(tod_ct, annot=True, fmt="d", cmap="Blues", ax=axes2[0,0],
            linewidths=0.3, cbar_kws={"shrink":0.8})
axes2[0,0].set_title("Crime frequency: Time of day × Crime type")
axes2[0,0].tick_params(axis="x", rotation=45)

# 4b. Weekday pattern
dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
dow = df["Day of Week"].value_counts().reindex(dow_order)
colors = [PALETTE[5] if d in ["Saturday","Sunday"] else PALETTE[0] for d in dow_order]
axes2[0,1].bar(dow.index, dow.values, color=colors)
axes2[0,1].set_title("Crimes by day of week")
axes2[0,1].tick_params(axis="x", rotation=35)
axes2[0,1].set_ylabel("Cases")

# 4c. Weapon vs casualties scatter
wep_stats = df.groupby("Weapon Type").agg(
    cases=("Weapon Type","count"),
    total_casualties=("Casualties","sum"),
    avg_response=("Police Response Time (mins)","mean")
).reset_index()
sc = axes2[0,2].scatter(wep_stats["cases"], wep_stats["total_casualties"],
                        s=wep_stats["avg_response"]*3, c=PALETTE[:len(wep_stats)], alpha=0.8)
for _, row in wep_stats.iterrows():
    axes2[0,2].annotate(row["Weapon Type"], (row["cases"], row["total_casualties"]),
                        fontsize=8, ha="center", va="bottom")
axes2[0,2].set_title("Weapon type: cases vs casualties\n(bubble = avg response time)")
axes2[0,2].set_xlabel("Number of cases"); axes2[0,2].set_ylabel("Total casualties")

# 4d. Suspect status breakdown
sus = df["Suspect Status"].value_counts()
axes2[1,0].pie(sus.values, labels=sus.index, autopct="%1.1f%%",
               colors=PALETTE[:len(sus)], startangle=90,
               wedgeprops={"edgecolor":"white","linewidth":1.5})
axes2[1,0].set_title("Suspect status distribution")

# 4e. Days to resolve distribution by case status
sns.violinplot(data=df, x="Case Status", y="Days to Resolve",
               palette=PALETTE[:4], ax=axes2[1,1], inner="box")
axes2[1,1].set_title("Days to resolve by case status")
axes2[1,1].tick_params(axis="x", rotation=20)

# 4f. Numeric correlation heatmap
num_cols = ["Number of Victims","Casualties","Injuries",
            "Property Loss (INR)","Police Response Time (mins)",
            "Officers Assigned","Days to Resolve","severity_score","conviction_bin"]
corr = df[num_cols].corr().round(2)
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
            center=0, ax=axes2[1,2], linewidths=0.3,
            cbar_kws={"shrink":0.8}, vmin=-1, vmax=1)
axes2[1,2].set_title("Numeric feature correlations")
axes2[1,2].tick_params(axis="x", rotation=45)

plt.tight_layout()
plt.savefig("eda_deepdive.png", dpi=130, bbox_inches="tight")
plt.close()
print("  ✓ eda_deepdive.png saved")

# ── 4. ML — Prepare features ──────────────────────────────────
print("\n" + "=" * 60)
print("  4. MACHINE LEARNING — FEATURE PREPARATION")
print("=" * 60)

le = LabelEncoder()
cat_cols = ["Crime Type","City","Season","Time of Day","Location Type",
            "Victim Age Group","Victim Gender","Weapon Type","Day Type"]
df_ml = df.copy()
for col in cat_cols:
    df_ml[col + "_enc"] = le.fit_transform(df_ml[col].astype(str))

feature_cols = [c + "_enc" for c in cat_cols] + [
    "severity_score","Number of Victims","Casualties","Injuries",
    "Property Loss (INR)","Police Response Time (mins)","Officers Assigned",
    "fast_response","multi_victim","high_value_loss","cctv_witness",
    "Repeat Offender_enc" if "Repeat Offender_enc" in df_ml.columns
    else "Weapon Involved_enc" if "Weapon Involved_enc" in df_ml.columns
    else "crime_month_num"
]
df_ml["Repeat Offender_enc"]  = (df_ml["Repeat Offender"]  == "Yes").astype(int)
df_ml["Weapon Involved_enc"]  = (df_ml["Weapon Involved"]  == "Yes").astype(int)
df_ml["CCTV_enc"]             = (df_ml["CCTV Available"]   == "Yes").astype(int)
df_ml["Witness_enc"]          = (df_ml["Witness Present"]  == "Yes").astype(int)

feature_cols = [c + "_enc" for c in cat_cols] + [
    "severity_score","Number of Victims","Casualties","Injuries",
    "Property Loss (INR)","Police Response Time (mins)","Officers Assigned",
    "fast_response","multi_victim","high_value_loss","cctv_witness",
    "Repeat Offender_enc","Weapon Involved_enc","CCTV_enc","Witness_enc","crime_month_num"
]

X = df_ml[feature_cols].fillna(0)
print(f"Feature matrix shape: {X.shape}")
print(f"Features used: {feature_cols}")

# ── 5. ML Model A: Conviction Predictor ───────────────────────
print("\n" + "=" * 60)
print("  5. ML MODEL A — CONVICTION PREDICTOR (Classification)")
print("=" * 60)

y_conv = df_ml["conviction_bin"]
X_tr, X_te, y_tr, y_te = train_test_split(X, y_conv, test_size=0.25, random_state=42, stratify=y_conv)

models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest":        RandomForestClassifier(n_estimators=100, random_state=42),
    "Gradient Boosting":    GradientBoostingClassifier(n_estimators=100, random_state=42),
}
best_model, best_score = None, 0
for name, model in models.items():
    cv = cross_val_score(model, X, y_conv, cv=5, scoring="accuracy")
    model.fit(X_tr, y_tr)
    test_acc = accuracy_score(y_te, model.predict(X_te))
    print(f"  {name:25s}  CV acc: {cv.mean():.3f} ± {cv.std():.3f}  |  Test acc: {test_acc:.3f}")
    if test_acc > best_score:
        best_score, best_model = test_acc, (name, model)

print(f"\n  Best model: {best_model[0]}  (test accuracy: {best_score:.3f})")
print("\n  Classification report (best model):")
print(classification_report(y_te, best_model[1].predict(X_te),
                             target_names=["Not Convicted","Convicted"]))

# Feature importances
rf_conv = RandomForestClassifier(n_estimators=100, random_state=42)
rf_conv.fit(X_tr, y_tr)
importances = pd.Series(rf_conv.feature_importances_, index=feature_cols).sort_values(ascending=False)
print("\n  Top 10 features (Random Forest):")
print(importances.head(10).round(4).to_string())

# ── 6. ML Model B: Severity Classifier ────────────────────────
print("\n" + "=" * 60)
print("  6. ML MODEL B — SEVERITY CLASSIFIER")
print("=" * 60)

y_sev = df_ml["severity_score"]
X_tr2, X_te2, y_tr2, y_te2 = train_test_split(X, y_sev, test_size=0.25, random_state=42)

rf_sev = RandomForestClassifier(n_estimators=150, random_state=42)
rf_sev.fit(X_tr2, y_tr2)
y_pred2 = rf_sev.predict(X_te2)
cv2 = cross_val_score(rf_sev, X, y_sev, cv=5, scoring="accuracy")

print(f"  CV accuracy: {cv2.mean():.3f} ± {cv2.std():.3f}")
print(f"  Test accuracy: {accuracy_score(y_te2, y_pred2):.3f}")
print("\n  Classification report:")
print(classification_report(y_te2, y_pred2, target_names=["Low","Medium","High","Critical"]))

# ── 7. ML Model C: Days-to-Resolve Regressor ──────────────────
print("\n" + "=" * 60)
print("  7. ML MODEL C — DAYS-TO-RESOLVE REGRESSOR")
print("=" * 60)

y_days = df_ml["Days to Resolve"]
X_tr3, X_te3, y_tr3, y_te3 = train_test_split(X, y_days, test_size=0.25, random_state=42)

rf_reg = RandomForestRegressor(n_estimators=150, random_state=42)
rf_reg.fit(X_tr3, y_tr3)
y_pred3 = rf_reg.predict(X_te3)

mae  = mean_absolute_error(y_te3, y_pred3)
r2   = r2_score(y_te3, y_pred3)
cv_r = cross_val_score(rf_reg, X, y_days, cv=5, scoring="r2")

print(f"  CV R²:    {cv_r.mean():.3f} ± {cv_r.std():.3f}")
print(f"  Test MAE: {mae:.1f} days")
print(f"  Test R²:  {r2:.3f}")

imp_reg = pd.Series(rf_reg.feature_importances_, index=feature_cols).sort_values(ascending=False)
print("\n  Top 10 predictors for resolution time:")
print(imp_reg.head(10).round(4).to_string())

# ── 8. ML summary plot ─────────────────────────────────────────
fig3, axes3 = plt.subplots(2, 2, figsize=(16, 12))
fig3.suptitle("Machine Learning Results", fontsize=16, fontweight="bold")

# 8a. Conviction feature importances
top10 = importances.head(10)
axes3[0,0].barh(top10.index[::-1], top10.values[::-1], color=PALETTE[0])
axes3[0,0].set_title("Conviction predictor — feature importances")
axes3[0,0].set_xlabel("Importance")

# 8b. Conviction confusion matrix
cm = confusion_matrix(y_te, best_model[1].predict(X_te))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=axes3[0,1],
            xticklabels=["Not Convicted","Convicted"],
            yticklabels=["Not Convicted","Convicted"])
axes3[0,1].set_title(f"Conviction confusion matrix\n({best_model[0]})")
axes3[0,1].set_ylabel("Actual"); axes3[0,1].set_xlabel("Predicted")

# 8c. Days-to-resolve: actual vs predicted
axes3[1,0].scatter(y_te3, y_pred3, alpha=0.5, color=PALETTE[2], edgecolors="none")
mn, mx = min(y_te3.min(), y_pred3.min()), max(y_te3.max(), y_pred3.max())
axes3[1,0].plot([mn,mx],[mn,mx], "r--", lw=1.5, label="Perfect fit")
axes3[1,0].set_title(f"Days to resolve — actual vs predicted\nMAE={mae:.1f}d, R²={r2:.3f}")
axes3[1,0].set_xlabel("Actual days"); axes3[1,0].set_ylabel("Predicted days")
axes3[1,0].legend()

# 8d. Model comparison bar
model_scores = {
    "Conviction\n(LR)":  cross_val_score(LogisticRegression(max_iter=1000),X,y_conv,cv=5).mean(),
    "Conviction\n(RF)":  cross_val_score(RandomForestClassifier(n_estimators=100,random_state=42),X,y_conv,cv=5).mean(),
    "Conviction\n(GBT)": cross_val_score(GradientBoostingClassifier(n_estimators=100),X,y_conv,cv=5).mean(),
    "Severity\n(RF)":    cv2.mean(),
}
bars = axes3[1,1].bar(model_scores.keys(), [v*100 for v in model_scores.values()],
                      color=PALETTE[:4], width=0.5, edgecolor="white")
axes3[1,1].set_title("Model accuracy comparison (5-fold CV %)")
axes3[1,1].set_ylabel("Accuracy %")
axes3[1,1].set_ylim(0, 100)
for bar, val in zip(bars, model_scores.values()):
    axes3[1,1].text(bar.get_x()+bar.get_width()/2, bar.get_height()+1,
                    f"{val*100:.1f}%", ha="center", fontsize=10, fontweight="bold")

plt.tight_layout()
plt.savefig("ml_results.png", dpi=130, bbox_inches="tight")
plt.close()
print("\n  ✓ ml_results.png saved")

# ── 9. Final summary ──────────────────────────────────────────
print("\n" + "=" * 60)
print("  8. KEY INSIGHTS SUMMARY")
print("=" * 60)
print("""
  DATA OVERVIEW
  ─────────────
  • 200 FIR cases | 12 cities | 2019–2024 | 33 variables
  • Most common crimes: Robbery (22), Vehicle Theft (19), Murder/Fraud (18)
  • Winter dominates (95 cases, 47.5%) — likely reporting bias

  EDA INSIGHTS
  ─────────────
  • Evening (17–21h) is peak crime time (65 cases)
  • Workplaces & religious places are highest-risk locations
  • Vehicles are the most common weapon type
  • Repeat offenders: 31% — significant recidivism signal

  OPERATIONAL METRICS
  ────────────────────
  • Overall conviction rate: 57%
  • Murder has highest conviction (77.8%) — likely more evidence
  • Burglary has lowest conviction (35.3%)
  • CCTV + Witness together → +7pp conviction lift
  • Mumbai has slowest avg response (73.5 min), Pune fastest (39.6)
  • Avg resolution: 172 days; 28.5% cases still open/under trial

  ML RESULTS
  ───────────
  • Conviction predictor (Gradient Boosting) ~65% test accuracy
  • Severity classifier (Random Forest) — see report above
  • Days-to-resolve regressor: MAE ~{:.0f} days, R² {:.2f}
  • Top conviction predictors: Response time, Officers assigned,
    Crime type, Severity, CCTV+Witness presence
""".format(mae, r2))

print("✓ Python EDA + ML complete. 3 plot files generated.")
=======
"""
=============================================================
  CRIME DATA ANALYTICS — PYTHON EDA + ML
  - Exploratory Data Analysis
  - Feature Engineering
  - ML: Conviction Predictor (Random Forest)
  - ML: Crime Severity Classifier
  - ML: Days-to-Resolve Regressor
=============================================================
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, confusion_matrix,
                             mean_absolute_error, r2_score, accuracy_score)
from sklearn.preprocessing import StandardScaler

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "font.size":        11,
    "axes.titlesize":   13,
    "axes.titleweight": "bold",
})
PALETTE = ["#378ADD","#7F77DD","#1D9E75","#D85A30","#BA7517","#A32D2D","#639922"]

# ── 1. Load & inspect ─────────────────────────────────────────
print("=" * 60)
print("  1. DATA LOADING & BASIC INSPECTION")
print("=" * 60)

df = pd.read_excel("crime_data.xlsx")
print(f"Shape         : {df.shape}")
print(f"Columns       : {list(df.columns)}")
print(f"\nData types:\n{df.dtypes.to_string()}")
print(f"\nNull values:\n{df.isnull().sum().to_string()}")
print(f"\nDescriptive stats (numeric):")
print(df.describe().round(2).to_string())

# ── 2. Feature Engineering ─────────────────────────────────────
print("\n" + "=" * 60)
print("  2. FEATURE ENGINEERING")
print("=" * 60)

df["Date of Crime"] = pd.to_datetime(df["Date of Crime"])
df["crime_month_num"]  = df["Date of Crime"].dt.month
df["high_value_loss"]  = (df["Property Loss (INR)"] > df["Property Loss (INR)"].median()).astype(int)
df["fast_response"]    = (df["Police Response Time (mins)"] <= 30).astype(int)
df["multi_victim"]     = (df["Number of Victims"] > 2).astype(int)
df["severity_score"]   = df["Severity"].map({"Low":1,"Medium":2,"High":3,"Critical":4})
df["conviction_bin"]   = (df["Conviction"] == "Yes").astype(int)
df["cctv_witness"]     = ((df["CCTV Available"]=="Yes") & (df["Witness Present"]=="Yes")).astype(int)

print("New features added:")
new_feats = ["crime_month_num","high_value_loss","fast_response",
             "multi_victim","severity_score","conviction_bin","cctv_witness"]
print(df[new_feats].describe().round(2).to_string())

# ── 3. EDA Plots ───────────────────────────────────────────────
print("\n" + "=" * 60)
print("  3. EXPLORATORY DATA ANALYSIS — generating plots …")
print("=" * 60)

# ---- Figure 1: Crime overview (2×3) --------------------------
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle("Crime Data — Exploratory Analysis", fontsize=16, fontweight="bold", y=1.01)

# 3a. Crime type bar
ct = df["Crime Type"].value_counts()
axes[0,0].barh(ct.index, ct.values, color=PALETTE[0])
axes[0,0].set_title("Crime type distribution")
axes[0,0].set_xlabel("Count")
for i, v in enumerate(ct.values):
    axes[0,0].text(v+0.2, i, str(v), va="center", fontsize=9)

# 3b. Year trend
yr = df["Year"].value_counts().sort_index()
axes[0,1].plot(yr.index, yr.values, marker="o", color=PALETTE[1], linewidth=2.5, markersize=8)
axes[0,1].fill_between(yr.index, yr.values, alpha=0.15, color=PALETTE[1])
axes[0,1].set_title("Annual crime trend")
axes[0,1].set_xlabel("Year"); axes[0,1].set_ylabel("Cases")

# 3c. Property loss distribution
axes[0,2].hist(df[df["Property Loss (INR)"]>0]["Property Loss (INR)"],
               bins=20, color=PALETTE[2], edgecolor="white")
axes[0,2].set_title("Property loss distribution (INR)")
axes[0,2].set_xlabel("Loss (INR)"); axes[0,2].set_ylabel("Frequency")

# 3d. Response time by city (boxplot)
city_order = df.groupby("City")["Police Response Time (mins)"].median().sort_values().index
sns.boxplot(data=df, y="City", x="Police Response Time (mins)",
            order=city_order, ax=axes[1,0], palette="Blues_r")
axes[1,0].set_title("Police response time by city")

# 3e. Conviction rate by crime type
conv = df.groupby("Crime Type")["conviction_bin"].mean().sort_values()
bars = axes[1,1].barh(conv.index, conv.values * 100,
                      color=[PALETTE[2] if v>=0.6 else PALETTE[4] if v>=0.5 else PALETTE[5]
                             for v in conv.values])
axes[1,1].set_title("Conviction rate by crime type (%)")
axes[1,1].set_xlabel("Conviction rate %")
axes[1,1].axvline(x=57, color="gray", linestyle="--", alpha=0.7, label="Overall avg")
axes[1,1].legend(fontsize=9)

# 3f. Severity × Season heatmap
pivot = df.groupby(["Season","Severity"]).size().unstack(fill_value=0)
pivot = pivot[["Low","Medium","High","Critical"]]
sns.heatmap(pivot, annot=True, fmt="d", cmap="YlOrRd", ax=axes[1,2], linewidths=0.5)
axes[1,2].set_title("Crime count: Season × Severity")

plt.tight_layout()
plt.savefig("eda_overview.png", dpi=130, bbox_inches="tight")
plt.close()
print("  ✓ eda_overview.png saved")

# ---- Figure 2: Deep-dive correlations & patterns -------------
fig2, axes2 = plt.subplots(2, 3, figsize=(18, 10))
fig2.suptitle("Crime Data — Deep-Dive Analysis", fontsize=16, fontweight="bold")

# 4a. Time of day × crime type heatmap
tod_ct = df.groupby(["Time of Day","Crime Type"]).size().unstack(fill_value=0)
sns.heatmap(tod_ct, annot=True, fmt="d", cmap="Blues", ax=axes2[0,0],
            linewidths=0.3, cbar_kws={"shrink":0.8})
axes2[0,0].set_title("Crime frequency: Time of day × Crime type")
axes2[0,0].tick_params(axis="x", rotation=45)

# 4b. Weekday pattern
dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
dow = df["Day of Week"].value_counts().reindex(dow_order)
colors = [PALETTE[5] if d in ["Saturday","Sunday"] else PALETTE[0] for d in dow_order]
axes2[0,1].bar(dow.index, dow.values, color=colors)
axes2[0,1].set_title("Crimes by day of week")
axes2[0,1].tick_params(axis="x", rotation=35)
axes2[0,1].set_ylabel("Cases")

# 4c. Weapon vs casualties scatter
wep_stats = df.groupby("Weapon Type").agg(
    cases=("Weapon Type","count"),
    total_casualties=("Casualties","sum"),
    avg_response=("Police Response Time (mins)","mean")
).reset_index()
sc = axes2[0,2].scatter(wep_stats["cases"], wep_stats["total_casualties"],
                        s=wep_stats["avg_response"]*3, c=PALETTE[:len(wep_stats)], alpha=0.8)
for _, row in wep_stats.iterrows():
    axes2[0,2].annotate(row["Weapon Type"], (row["cases"], row["total_casualties"]),
                        fontsize=8, ha="center", va="bottom")
axes2[0,2].set_title("Weapon type: cases vs casualties\n(bubble = avg response time)")
axes2[0,2].set_xlabel("Number of cases"); axes2[0,2].set_ylabel("Total casualties")

# 4d. Suspect status breakdown
sus = df["Suspect Status"].value_counts()
axes2[1,0].pie(sus.values, labels=sus.index, autopct="%1.1f%%",
               colors=PALETTE[:len(sus)], startangle=90,
               wedgeprops={"edgecolor":"white","linewidth":1.5})
axes2[1,0].set_title("Suspect status distribution")

# 4e. Days to resolve distribution by case status
sns.violinplot(data=df, x="Case Status", y="Days to Resolve",
               palette=PALETTE[:4], ax=axes2[1,1], inner="box")
axes2[1,1].set_title("Days to resolve by case status")
axes2[1,1].tick_params(axis="x", rotation=20)

# 4f. Numeric correlation heatmap
num_cols = ["Number of Victims","Casualties","Injuries",
            "Property Loss (INR)","Police Response Time (mins)",
            "Officers Assigned","Days to Resolve","severity_score","conviction_bin"]
corr = df[num_cols].corr().round(2)
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
            center=0, ax=axes2[1,2], linewidths=0.3,
            cbar_kws={"shrink":0.8}, vmin=-1, vmax=1)
axes2[1,2].set_title("Numeric feature correlations")
axes2[1,2].tick_params(axis="x", rotation=45)

plt.tight_layout()
plt.savefig("eda_deepdive.png", dpi=130, bbox_inches="tight")
plt.close()
print("  ✓ eda_deepdive.png saved")

# ── 4. ML — Prepare features ──────────────────────────────────
print("\n" + "=" * 60)
print("  4. MACHINE LEARNING — FEATURE PREPARATION")
print("=" * 60)

le = LabelEncoder()
cat_cols = ["Crime Type","City","Season","Time of Day","Location Type",
            "Victim Age Group","Victim Gender","Weapon Type","Day Type"]
df_ml = df.copy()
for col in cat_cols:
    df_ml[col + "_enc"] = le.fit_transform(df_ml[col].astype(str))

feature_cols = [c + "_enc" for c in cat_cols] + [
    "severity_score","Number of Victims","Casualties","Injuries",
    "Property Loss (INR)","Police Response Time (mins)","Officers Assigned",
    "fast_response","multi_victim","high_value_loss","cctv_witness",
    "Repeat Offender_enc" if "Repeat Offender_enc" in df_ml.columns
    else "Weapon Involved_enc" if "Weapon Involved_enc" in df_ml.columns
    else "crime_month_num"
]
df_ml["Repeat Offender_enc"]  = (df_ml["Repeat Offender"]  == "Yes").astype(int)
df_ml["Weapon Involved_enc"]  = (df_ml["Weapon Involved"]  == "Yes").astype(int)
df_ml["CCTV_enc"]             = (df_ml["CCTV Available"]   == "Yes").astype(int)
df_ml["Witness_enc"]          = (df_ml["Witness Present"]  == "Yes").astype(int)

feature_cols = [c + "_enc" for c in cat_cols] + [
    "severity_score","Number of Victims","Casualties","Injuries",
    "Property Loss (INR)","Police Response Time (mins)","Officers Assigned",
    "fast_response","multi_victim","high_value_loss","cctv_witness",
    "Repeat Offender_enc","Weapon Involved_enc","CCTV_enc","Witness_enc","crime_month_num"
]

X = df_ml[feature_cols].fillna(0)
print(f"Feature matrix shape: {X.shape}")
print(f"Features used: {feature_cols}")

# ── 5. ML Model A: Conviction Predictor ───────────────────────
print("\n" + "=" * 60)
print("  5. ML MODEL A — CONVICTION PREDICTOR (Classification)")
print("=" * 60)

y_conv = df_ml["conviction_bin"]
X_tr, X_te, y_tr, y_te = train_test_split(X, y_conv, test_size=0.25, random_state=42, stratify=y_conv)

models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest":        RandomForestClassifier(n_estimators=100, random_state=42),
    "Gradient Boosting":    GradientBoostingClassifier(n_estimators=100, random_state=42),
}
best_model, best_score = None, 0
for name, model in models.items():
    cv = cross_val_score(model, X, y_conv, cv=5, scoring="accuracy")
    model.fit(X_tr, y_tr)
    test_acc = accuracy_score(y_te, model.predict(X_te))
    print(f"  {name:25s}  CV acc: {cv.mean():.3f} ± {cv.std():.3f}  |  Test acc: {test_acc:.3f}")
    if test_acc > best_score:
        best_score, best_model = test_acc, (name, model)

print(f"\n  Best model: {best_model[0]}  (test accuracy: {best_score:.3f})")
print("\n  Classification report (best model):")
print(classification_report(y_te, best_model[1].predict(X_te),
                             target_names=["Not Convicted","Convicted"]))

# Feature importances
rf_conv = RandomForestClassifier(n_estimators=100, random_state=42)
rf_conv.fit(X_tr, y_tr)
importances = pd.Series(rf_conv.feature_importances_, index=feature_cols).sort_values(ascending=False)
print("\n  Top 10 features (Random Forest):")
print(importances.head(10).round(4).to_string())

# ── 6. ML Model B: Severity Classifier ────────────────────────
print("\n" + "=" * 60)
print("  6. ML MODEL B — SEVERITY CLASSIFIER")
print("=" * 60)

y_sev = df_ml["severity_score"]
X_tr2, X_te2, y_tr2, y_te2 = train_test_split(X, y_sev, test_size=0.25, random_state=42)

rf_sev = RandomForestClassifier(n_estimators=150, random_state=42)
rf_sev.fit(X_tr2, y_tr2)
y_pred2 = rf_sev.predict(X_te2)
cv2 = cross_val_score(rf_sev, X, y_sev, cv=5, scoring="accuracy")

print(f"  CV accuracy: {cv2.mean():.3f} ± {cv2.std():.3f}")
print(f"  Test accuracy: {accuracy_score(y_te2, y_pred2):.3f}")
print("\n  Classification report:")
print(classification_report(y_te2, y_pred2, target_names=["Low","Medium","High","Critical"]))

# ── 7. ML Model C: Days-to-Resolve Regressor ──────────────────
print("\n" + "=" * 60)
print("  7. ML MODEL C — DAYS-TO-RESOLVE REGRESSOR")
print("=" * 60)

y_days = df_ml["Days to Resolve"]
X_tr3, X_te3, y_tr3, y_te3 = train_test_split(X, y_days, test_size=0.25, random_state=42)

rf_reg = RandomForestRegressor(n_estimators=150, random_state=42)
rf_reg.fit(X_tr3, y_tr3)
y_pred3 = rf_reg.predict(X_te3)

mae  = mean_absolute_error(y_te3, y_pred3)
r2   = r2_score(y_te3, y_pred3)
cv_r = cross_val_score(rf_reg, X, y_days, cv=5, scoring="r2")

print(f"  CV R²:    {cv_r.mean():.3f} ± {cv_r.std():.3f}")
print(f"  Test MAE: {mae:.1f} days")
print(f"  Test R²:  {r2:.3f}")

imp_reg = pd.Series(rf_reg.feature_importances_, index=feature_cols).sort_values(ascending=False)
print("\n  Top 10 predictors for resolution time:")
print(imp_reg.head(10).round(4).to_string())

# ── 8. ML summary plot ─────────────────────────────────────────
fig3, axes3 = plt.subplots(2, 2, figsize=(16, 12))
fig3.suptitle("Machine Learning Results", fontsize=16, fontweight="bold")

# 8a. Conviction feature importances
top10 = importances.head(10)
axes3[0,0].barh(top10.index[::-1], top10.values[::-1], color=PALETTE[0])
axes3[0,0].set_title("Conviction predictor — feature importances")
axes3[0,0].set_xlabel("Importance")

# 8b. Conviction confusion matrix
cm = confusion_matrix(y_te, best_model[1].predict(X_te))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=axes3[0,1],
            xticklabels=["Not Convicted","Convicted"],
            yticklabels=["Not Convicted","Convicted"])
axes3[0,1].set_title(f"Conviction confusion matrix\n({best_model[0]})")
axes3[0,1].set_ylabel("Actual"); axes3[0,1].set_xlabel("Predicted")

# 8c. Days-to-resolve: actual vs predicted
axes3[1,0].scatter(y_te3, y_pred3, alpha=0.5, color=PALETTE[2], edgecolors="none")
mn, mx = min(y_te3.min(), y_pred3.min()), max(y_te3.max(), y_pred3.max())
axes3[1,0].plot([mn,mx],[mn,mx], "r--", lw=1.5, label="Perfect fit")
axes3[1,0].set_title(f"Days to resolve — actual vs predicted\nMAE={mae:.1f}d, R²={r2:.3f}")
axes3[1,0].set_xlabel("Actual days"); axes3[1,0].set_ylabel("Predicted days")
axes3[1,0].legend()

# 8d. Model comparison bar
model_scores = {
    "Conviction\n(LR)":  cross_val_score(LogisticRegression(max_iter=1000),X,y_conv,cv=5).mean(),
    "Conviction\n(RF)":  cross_val_score(RandomForestClassifier(n_estimators=100,random_state=42),X,y_conv,cv=5).mean(),
    "Conviction\n(GBT)": cross_val_score(GradientBoostingClassifier(n_estimators=100),X,y_conv,cv=5).mean(),
    "Severity\n(RF)":    cv2.mean(),
}
bars = axes3[1,1].bar(model_scores.keys(), [v*100 for v in model_scores.values()],
                      color=PALETTE[:4], width=0.5, edgecolor="white")
axes3[1,1].set_title("Model accuracy comparison (5-fold CV %)")
axes3[1,1].set_ylabel("Accuracy %")
axes3[1,1].set_ylim(0, 100)
for bar, val in zip(bars, model_scores.values()):
    axes3[1,1].text(bar.get_x()+bar.get_width()/2, bar.get_height()+1,
                    f"{val*100:.1f}%", ha="center", fontsize=10, fontweight="bold")

plt.tight_layout()
plt.savefig("ml_results.png", dpi=130, bbox_inches="tight")
plt.close()
print("\n  ✓ ml_results.png saved")

# ── 9. Final summary ──────────────────────────────────────────
print("\n" + "=" * 60)
print("  8. KEY INSIGHTS SUMMARY")
print("=" * 60)
print("""
  DATA OVERVIEW
  ─────────────
  • 200 FIR cases | 12 cities | 2019–2024 | 33 variables
  • Most common crimes: Robbery (22), Vehicle Theft (19), Murder/Fraud (18)
  • Winter dominates (95 cases, 47.5%) — likely reporting bias

  EDA INSIGHTS
  ─────────────
  • Evening (17–21h) is peak crime time (65 cases)
  • Workplaces & religious places are highest-risk locations
  • Vehicles are the most common weapon type
  • Repeat offenders: 31% — significant recidivism signal

  OPERATIONAL METRICS
  ────────────────────
  • Overall conviction rate: 57%
  • Murder has highest conviction (77.8%) — likely more evidence
  • Burglary has lowest conviction (35.3%)
  • CCTV + Witness together → +7pp conviction lift
  • Mumbai has slowest avg response (73.5 min), Pune fastest (39.6)
  • Avg resolution: 172 days; 28.5% cases still open/under trial

  ML RESULTS
  ───────────
  • Conviction predictor (Gradient Boosting) ~65% test accuracy
  • Severity classifier (Random Forest) — see report above
  • Days-to-resolve regressor: MAE ~{:.0f} days, R² {:.2f}
  • Top conviction predictors: Response time, Officers assigned,
    Crime type, Severity, CCTV+Witness presence
""".format(mae, r2))

print("✓ Python EDA + ML complete. 3 plot files generated.")
>>>>>>> 640c70f3fdd4027bf2402a64d8c57b82eb9a02de

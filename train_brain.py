import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import classification_report
from sklearn.feature_selection import SelectKBest, f_classif
import joblib
import numpy as np
import os
print("SOLARSERVER AI TRAINER - ADVANCED ENSEMBLE VERSION")
print("=" * 55)
url_train = "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTrain+.txt"
url_test = "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTest+.txt"
local_train = "KDDTrain+.txt"
local_test = "KDDTest+.txt"
cols = ['duration','protocol_type','service','flag','src_bytes','dst_bytes','land','wrong_fragment','urgent','hot','num_failed_logins','logged_in','num_compromised','root_shell','su_attempted','num_root','num_file_creations','num_shells','num_access_files','num_outbound_cmds','is_host_login','is_guest_login','count','srv_count','serror_rate','srv_serror_rate','rerror_rate','srv_rerror_rate','same_srv_rate','diff_srv_rate','srv_diff_host_rate','dst_host_count','dst_host_srv_count','dst_host_same_srv_rate','dst_host_diff_srv_rate','dst_host_same_src_port_rate','dst_host_srv_diff_host_rate','dst_host_serror_rate','dst_host_srv_serror_rate','dst_host_rerror_rate','dst_host_srv_rerror_rate','label','difficulty']

dfs = []
for url, local_file, name in [(url_train, local_train, "train"), (url_test, local_test, "test")]:
    if os.path.exists(local_file):
        print(f"Loading local {name} dataset...")
        df = pd.read_csv(local_file, names=cols, header=None)
        print(f"Loaded {len(df)} {name} samples from local file")
    else:
        try:
            print(f"Downloading {name} dataset...")
            df = pd.read_csv(url, names=cols, header=None)
            df.to_csv(local_file, index=False, header=False)
            print(f"Downloaded and saved {len(df)} {name} samples")
        except Exception as e:
            print(f"Download failed for {name}: {e}")
            continue
    dfs.append(df)

if len(dfs) == 0:
    print("No datasets loaded, using synthetic data...")
    np.random.seed(42)
    n = 5000
    X = np.column_stack([
        np.random.exponential(100, n),
        np.random.choice([0,1,2], n),
        np.random.choice(range(10), n),
        np.random.choice(range(5), n),
        np.random.exponential(1000, n),
        np.random.exponential(5000, n),
        np.random.choice([0,1], n),
        np.random.choice([0,1], n),
        np.random.choice([0,1], n),
        np.random.choice([0,5], n),
        np.random.choice([0,1], n),
        np.random.choice([0,1], n),
        np.random.choice([0,10], n),
        np.random.choice([0,1], n),
        np.random.choice([0,1], n),
        np.random.choice([0,5], n),
        np.random.choice([0,5], n),
        np.random.choice([0,2], n),
        np.random.choice([0,5], n),
        np.zeros(n),
        np.random.choice([0,1], n),
        np.random.choice([0,1], n),
        np.random.randint(1, 50, n),
        np.random.randint(1, 50, n),
        np.random.uniform(0, 1, n),
        np.random.uniform(0, 1, n),
        np.random.uniform(0, 1, n),
        np.random.uniform(0, 1, n),
        np.random.uniform(0, 1, n),
        np.random.uniform(0, 1, n),
        np.random.uniform(0, 1, n),
        np.random.randint(1, 255, n),
        np.random.randint(1, 255, n),
        np.random.uniform(0, 1, n),
        np.random.uniform(0, 1, n),
        np.random.uniform(0, 1, n),
        np.random.uniform(0, 1, n),
        np.random.uniform(0, 1, n),
        np.random.uniform(0, 1, n),
        np.random.uniform(0, 1, n),
        np.random.uniform(0, 1, n),
    ])
    y = np.random.choice([0,1], n, p=[0.1, 0.9])
    encoders = {}
    print(f"Generated {n} samples")
else:
    # Combine train and test for more data
    df = pd.concat(dfs, ignore_index=True)
    print(f"Combined dataset: {len(df)} samples")
    
    # Features: all except label and difficulty
    feature_cols = [col for col in cols if col not in ['label', 'difficulty']]
    
    # Sample test cases from real data BEFORE encoding
    normal_sample = df[df['label'] == 'normal'].iloc[0][feature_cols].to_dict()
    attack_sample = df[df['label'] != 'normal'].iloc[0][feature_cols].to_dict()
    
    # Preprocess data
    df['label'] = df['label'].apply(lambda x: 1 if x == 'normal' else 0)
    
    # Encode categorical features
    categorical_cols = ['protocol_type', 'service', 'flag']
    encoders = {}
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        encoders[col] = le
    
    X = df[feature_cols].values
    y = df['label'].values

print("\nAdvanced Training with Feature Selection and Tuning...")
sc = StandardScaler()
Xs = sc.fit_transform(X)

# Feature selection
selector = SelectKBest(score_func=f_classif, k=30)  # Select top 30 features
Xs_selected = selector.fit_transform(Xs, y)
selected_features = selector.get_support(indices=True)
print(f"Selected {len(selected_features)} best features")

# Hyperparameter tuning for RandomForest
param_grid = {
    'n_estimators': [100, 200],
    'max_depth': [10, 20, None],
    'min_samples_split': [2, 5],
    'min_samples_leaf': [1, 2]
}
clf = RandomForestClassifier(random_state=42, n_jobs=-1)
grid_search = GridSearchCV(clf, param_grid, cv=3, scoring='accuracy', n_jobs=-1)
grid_search.fit(Xs_selected, y)
best_clf = grid_search.best_estimator_
print(f"Best parameters: {grid_search.best_params_}")
print(f"Best CV score: {grid_search.best_score_:.4f}")

# Cross-validation with best model
cv_scores = cross_val_score(best_clf, Xs_selected, y, cv=5, scoring='accuracy')
print(f"Cross-validation accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

# Final evaluation
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(Xs_selected, y, test_size=0.2, random_state=42, stratify=y)
best_clf.fit(X_train, y_train)
y_pred = best_clf.predict(X_test)
print("Final Validation Report:")
print(classification_report(y_test, y_pred, target_names=['Attack', 'Normal']))

joblib.dump(best_clf, "SolarServer_model.pkl")
joblib.dump(sc, "SolarServer_scaler.pkl")
joblib.dump(encoders, "SolarServer_encoders.pkl")
joblib.dump(selector, "SolarServer_selector.pkl")
print("Advanced model saved with feature selection and hyperparameter tuning")

print("\nTesting...")
if 'normal_sample' in locals() and 'attack_sample' in locals():
    def preprocess_sample(sample, encoders, scaler, selector):
        df_sample = pd.DataFrame([sample])
        for col, enc in encoders.items():
            if col in df_sample.columns:
                df_sample[col] = enc.transform(df_sample[col])
        X_sample = df_sample.values
        X_scaled = scaler.transform(X_sample)
        return selector.transform(X_scaled)
    
    normal_processed = preprocess_sample(normal_sample, encoders, sc, selector)
    attack_processed = preprocess_sample(attack_sample, encoders, sc, selector)
    pred_normal = best_clf.predict(normal_processed)[0]
    pred_attack = best_clf.predict(attack_processed)[0]
    print(f"   Normal sample: {'SAFE' if pred_normal == 1 else 'THREAT'}")
    print(f"   Attack sample: {'SAFE' if pred_attack == 1 else 'THREAT'}")
    
    # Show probabilities
    prob_normal = best_clf.predict_proba(normal_processed)[0]
    prob_attack = best_clf.predict_proba(attack_processed)[0]
    print(f"   Normal confidence: {prob_normal[1]:.4f} (SAFE)")
    print(f"   Attack confidence: {prob_attack[0]:.4f} (THREAT)")
else:
    print("   Skipping test predictions with synthetic data")

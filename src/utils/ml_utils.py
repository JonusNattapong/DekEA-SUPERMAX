import numpy as np
import pandas as pd
import itertools

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.utils import to_categorical
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

# --- Sequence Preparation Utility ---
def prepare_sequences(data: pd.DataFrame, feature_cols, lookback=30, label_col='label', dropna=True):
    """
    สร้าง sequence สำหรับ deep learning เช่น LSTM/GRU
    คืนค่า X, y พร้อม shape ที่เหมาะสม
    """
    if dropna:
        data = data.dropna()
    X, y = [], []
    values = data[feature_cols].values
    labels = data[label_col].values
    for i in range(lookback, len(data)):
        X.append(values[i-lookback:i])
        y.append(labels[i])
    return np.array(X), np.array(y)

# --- Simple Grid Search Hyperparameter Tuning ---
def auto_hyperparameter_tune(
    data: pd.DataFrame,
    model_type='LSTM',
    feature_cols=None,
    lookback_choices=[20, 30],
    units_choices=[16, 32],
    dropout_choices=[0.1, 0.2],
    batch_size_choices=[16, 32],
    epochs_choices=[10, 20],
    label_col='label',
    verbose=0
):
    """
    ทดลองเทรน LSTM/GRU หลายชุด hyperparameter และคืนค่าที่ดีที่สุด (accuracy สูงสุด)
    """
    if not TENSORFLOW_AVAILABLE:
        raise ImportError('tensorflow is not installed')
    if feature_cols is None:
        feature_cols = ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
    best_acc = 0
    best_params = None
    best_model = None
    results = []
    for lookback, units, dropout, batch_size, epochs in itertools.product(
        lookback_choices, units_choices, dropout_choices, batch_size_choices, epochs_choices
    ):
        try:
            X, y = prepare_sequences(data, feature_cols, lookback, label_col)
            y_cat = to_categorical(y, num_classes=3)
            model = Sequential()
            if model_type == 'LSTM':
                model.add(LSTM(units, input_shape=(lookback, len(feature_cols)), return_sequences=False))
            elif model_type == 'GRU':
                model.add(GRU(units, input_shape=(lookback, len(feature_cols)), return_sequences=False))
            else:
                continue
            model.add(Dropout(dropout))
            model.add(Dense(16, activation='relu'))
            model.add(Dense(3, activation='softmax'))
            model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
            model.fit(X, y_cat, epochs=epochs, batch_size=batch_size, verbose=verbose)
            loss, acc = model.evaluate(X, y_cat, verbose=0)
            results.append({'params': (lookback, units, dropout, batch_size, epochs), 'acc': acc})
            if acc > best_acc:
                best_acc = acc
                best_params = (lookback, units, dropout, batch_size, epochs)
                best_model = model
        except Exception as e:
            continue
    return best_model, best_params, best_acc, results

# --- Auto Hyperparameter Tuning for Tree-based ML ---
def auto_hyperparameter_tune_tree(
    data: pd.DataFrame,
    model_type='XGBoost',
    feature_cols=None,
    n_estimators_choices=[50, 100],
    max_depth_choices=[3, 5],
    learning_rate_choices=[0.05, 0.1],
    label_col='label',
    verbose=0
):
    """
    ทดลองเทรน ML tree-based หลายชุด hyperparameter และคืนค่าที่ดีที่สุด (accuracy สูงสุด)
    รองรับ XGBoost, LightGBM, CatBoost, ExtraTrees, RandomForest
    """
    import warnings
    warnings.filterwarnings('ignore')
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    try:
        import xgboost as xgb
    except ImportError:
        xgb = None
    try:
        import lightgbm as lgb
    except ImportError:
        lgb = None
    try:
        from catboost import CatBoostClassifier
    except ImportError:
        CatBoostClassifier = None
    from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
    if feature_cols is None:
        feature_cols = ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
    df = data.copy().dropna()
    X = df[feature_cols]
    y = df[label_col]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    best_acc = 0
    best_params = None
    best_model = None
    results = []
    for n_estimators in n_estimators_choices:
        for max_depth in max_depth_choices:
            for learning_rate in learning_rate_choices:
                try:
                    if model_type == 'XGBoost' and xgb is not None:
                        model = xgb.XGBClassifier(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, use_label_encoder=False, eval_metric='mlogloss')
                    elif model_type == 'LightGBM' and lgb is not None:
                        model = lgb.LGBMClassifier(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate)
                    elif model_type == 'CatBoost' and CatBoostClassifier is not None:
                        model = CatBoostClassifier(iterations=n_estimators, depth=max_depth, learning_rate=learning_rate, verbose=0)
                    elif model_type == 'ExtraTrees':
                        model = ExtraTreesClassifier(n_estimators=n_estimators, max_depth=max_depth)
                    elif model_type == 'RandomForest':
                        model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth)
                    else:
                        continue
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                    acc = accuracy_score(y_test, y_pred)
                    results.append({'params': (n_estimators, max_depth, learning_rate), 'acc': acc})
                    if acc > best_acc:
                        best_acc = acc
                        best_params = (n_estimators, max_depth, learning_rate)
                        best_model = model
                except Exception as e:
                    continue
    return best_model, best_params, best_acc, results

# --- Optuna Hyperparameter Tuning for Tree-based ML ---

def auto_hyperparameter_tune_optuna_lstm(
    data: pd.DataFrame,
    feature_cols=None,
    label_col='label',
    n_trials=20,
    direction='maximize',
    random_state=42,
    verbose=0
):
    """
    ใช้ Optuna เพื่อ tuning hyperparameter สำหรับ LSTM (deep learning)
    คืน best_model, best_params, best_acc, study
    """
    import optuna
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.utils import to_categorical
    import numpy as np
    if feature_cols is None:
        feature_cols = ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
    df = data.copy().dropna()
    def objective(trial):
        lookback = trial.suggest_int('lookback', 10, 60)
        units = trial.suggest_int('units', 16, 64)
        dropout = trial.suggest_float('dropout', 0.1, 0.5)
        batch_size = trial.suggest_categorical('batch_size', [16, 32, 64])
        epochs = trial.suggest_int('epochs', 10, 30)
        X, y = prepare_sequences(df, feature_cols, lookback, label_col)
        if len(X) == 0:
            return 0.0
        y_cat = to_categorical(y, num_classes=3)
        model = Sequential([
            LSTM(units, input_shape=(lookback, len(feature_cols))),
            Dropout(dropout),
            Dense(16, activation='relu'),
            Dense(3, activation='softmax')
        ])
        model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
        model.fit(X, y_cat, epochs=epochs, batch_size=batch_size, verbose=0)
        loss, acc = model.evaluate(X, y_cat, verbose=0)
        return acc
    study = optuna.create_study(direction=direction)
    study.optimize(objective, n_trials=n_trials)
    best_params = study.best_params
    lookback = best_params['lookback']
    units = best_params['units']
    dropout = best_params['dropout']
    batch_size = best_params['batch_size']
    epochs = best_params['epochs']
    X, y = prepare_sequences(df, feature_cols, lookback, label_col)
    y_cat = to_categorical(y, num_classes=3)
    best_model = Sequential([
        LSTM(units, input_shape=(lookback, len(feature_cols))),
        Dropout(dropout),
        Dense(16, activation='relu'),
        Dense(3, activation='softmax')
    ])
    best_model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
    best_model.fit(X, y_cat, epochs=epochs, batch_size=batch_size, verbose=0)
    loss, best_acc = best_model.evaluate(X, y_cat, verbose=0)
    return best_model, best_params, best_acc, study

def auto_hyperparameter_tune_optuna(
    data: pd.DataFrame,
    model_type='XGBoost',
    feature_cols=None,
    label_col='label',
    n_trials=30,
    direction='maximize',
    random_state=42,
    verbose=0
):
    """
    ใช้ Optuna เพื่อ tuning hyperparameter สำหรับ XGBoost, LightGBM, CatBoost
    คืน best_model, best_params, best_acc, study
    """
    import optuna
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    try:
        import xgboost as xgb
    except ImportError:
        xgb = None
    try:
        import lightgbm as lgb
    except ImportError:
        lgb = None
    try:
        from catboost import CatBoostClassifier
    except ImportError:
        CatBoostClassifier = None
    if feature_cols is None:
        feature_cols = ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
    df = data.copy().dropna()
    X = df[feature_cols]
    y = df[label_col]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=random_state)

    def objective(trial):
        n_estimators = trial.suggest_int('n_estimators', 50, 300)
        max_depth = trial.suggest_int('max_depth', 3, 10)
        learning_rate = trial.suggest_float('learning_rate', 0.01, 0.2)
        if model_type == 'XGBoost' and xgb is not None:
            model = xgb.XGBClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                use_label_encoder=False,
                eval_metric='mlogloss',
                random_state=random_state
            )
        elif model_type == 'LightGBM' and lgb is not None:
            model = lgb.LGBMClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                random_state=random_state
            )
        elif model_type == 'CatBoost' and CatBoostClassifier is not None:
            model = CatBoostClassifier(
                iterations=n_estimators,
                depth=max_depth,
                learning_rate=learning_rate,
                verbose=0,
                random_state=random_state
            )
        else:
            raise ValueError('Unsupported model_type or missing library')
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        return acc

    study = optuna.create_study(direction=direction)
    study.optimize(objective, n_trials=n_trials)
    best_params = study.best_params
    # สร้างโมเดลที่ดีที่สุดใหม่ด้วย best_params
    n_estimators = best_params['n_estimators']
    max_depth = best_params['max_depth']
    learning_rate = best_params['learning_rate']
    if model_type == 'XGBoost' and xgb is not None:
        best_model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            use_label_encoder=False,
            eval_metric='mlogloss',
            random_state=random_state
        )
    elif model_type == 'LightGBM' and lgb is not None:
        best_model = lgb.LGBMClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state
        )
    elif model_type == 'CatBoost' and CatBoostClassifier is not None:
        best_model = CatBoostClassifier(
            iterations=n_estimators,
            depth=max_depth,
            learning_rate=learning_rate,
            verbose=0,
            random_state=random_state
        )
    else:
        best_model = None
    if best_model is not None:
        best_model.fit(X_train, y_train)
        y_pred = best_model.predict(X_test)
        best_acc = accuracy_score(y_test, y_pred)
    else:
        best_acc = None
    return best_model, best_params, best_acc, study

# Example usage:
# best_model, best_params, best_acc, study = auto_hyperparameter_tune_optuna(historical_df, model_type='XGBoost', n_trials=30)
# print('Best:', best_params, 'Accuracy:', best_acc)

# 🚀 DEPLOYMENT GUIDE

Step-by-step guide to deploy SOC ML models in production.

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### System Requirements
- [ ] Python 3.8 or higher
- [ ] 4GB+ RAM (8GB+ recommended)
- [ ] CPU: 2+ cores (4+ recommended for high throughput)
- [ ] Disk: 500MB for models + space for logs

### Dependencies
```bash
pip install numpy>=1.21.0
pip install pandas>=1.3.0
pip install scikit-learn>=1.0.0
```

### Optional (for better performance)
```bash
pip install joblib  # Faster model loading
pip install flask   # For REST API deployment
```

---

## 🔧 DEPLOYMENT OPTIONS

### Option 1: Direct Python Integration (Simplest)
Integrate models directly into your Python application.

### Option 2: REST API Service (Recommended)
Deploy as a microservice with REST API.

### Option 3: Streaming Pipeline (Advanced)
Integrate with Apache Kafka, Spark, or similar.

---

## 📦 OPTION 1: Direct Python Integration

### Step 1: Copy Model Files
```bash
# Copy entire folder to your application
cp -r DEPLOY_READY_SOC_MODELS/ /path/to/your/app/models/
```

### Step 2: Create Model Loader Class
```python
# soc_models.py
import pickle
from pathlib import Path

class SOCModels:
    def __init__(self, model_dir):
        self.model_dir = Path(model_dir)
        self.models = {}
        self.preprocessors = {}
        self._load_all_models()
    
    def _load_all_models(self):
        """Load all models and preprocessors"""
        # Multi-OS Log Anomaly
        with open(self.model_dir / 'multi_os_log_anomaly_detector.pkl', 'rb') as f:
            self.models['log_anomaly'] = pickle.load(f)
        with open(self.model_dir / 'multi_os_log_anomaly_scaler.pkl', 'rb') as f:
            self.preprocessors['log_anomaly'] = pickle.load(f)
        
        # Text Log Anomaly
        with open(self.model_dir / 'text_log_anomaly_detector.pkl', 'rb') as f:
            self.models['text_anomaly'] = pickle.load(f)
        with open(self.model_dir / 'text_log_tfidf_vectorizer.pkl', 'rb') as f:
            self.preprocessors['text_anomaly'] = pickle.load(f)
        
        # Add other models as needed...
    
    def detect_log_anomaly(self, features):
        """Detect log anomalies from structured features"""
        scaled = self.preprocessors['log_anomaly'].transform(features)
        prediction = self.models['log_anomaly'].predict(scaled)
        probability = self.models['log_anomaly'].predict_proba(scaled)
        return prediction, probability
    
    def detect_text_anomaly(self, log_texts):
        """Detect anomalies from log text"""
        vectorized = self.preprocessors['text_anomaly'].transform(log_texts)
        prediction = self.models['text_anomaly'].predict(vectorized)
        probability = self.models['text_anomaly'].predict_proba(vectorized)
        return prediction, probability
```

### Step 3: Use in Your Application
```python
from soc_models import SOCModels
import numpy as np

# Initialize models
soc = SOCModels('path/to/DEPLOY_READY_SOC_MODELS')

# Example: Detect log anomaly
log_features = np.array([[...]])  # Your feature extraction
prediction, probability = soc.detect_log_anomaly(log_features)

if prediction[0] == 1:
    # Trigger alert
    send_alert(f"Log anomaly detected! Confidence: {probability[0][1]:.1%}")
```

---

## 🌐 OPTION 2: REST API Service (Recommended)

### Step 1: Create Flask API
```python
# app.py
from flask import Flask, request, jsonify
import pickle
import numpy as np
from pathlib import Path

app = Flask(__name__)

# Load models at startup
MODEL_DIR = Path('DEPLOY_READY_SOC_MODELS')

models = {
    'log_anomaly': pickle.load(open(MODEL_DIR / 'multi_os_log_anomaly_detector.pkl', 'rb')),
    'text_anomaly': pickle.load(open(MODEL_DIR / 'text_log_anomaly_detector.pkl', 'rb')),
    'insider_threat': pickle.load(open(MODEL_DIR / 'insider_threat_detector.pkl', 'rb')),
    'web_attack': pickle.load(open(MODEL_DIR / 'web_attack_detector.pkl', 'rb')),
}

preprocessors = {
    'log_anomaly': pickle.load(open(MODEL_DIR / 'multi_os_log_anomaly_scaler.pkl', 'rb')),
    'text_anomaly': pickle.load(open(MODEL_DIR / 'text_log_tfidf_vectorizer.pkl', 'rb')),
    'insider_threat': pickle.load(open(MODEL_DIR / 'insider_threat_scaler.pkl', 'rb')),
    'web_attack': pickle.load(open(MODEL_DIR / 'web_attack_scaler.pkl', 'rb')),
}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'models_loaded': len(models)})

@app.route('/detect/log_anomaly', methods=['POST'])
def detect_log_anomaly():
    """
    POST /detect/log_anomaly
    Body: {"features": [[feature1, feature2, ..., feature11]]}
    """
    data = request.json
    features = np.array(data['features'])
    
    scaled = preprocessors['log_anomaly'].transform(features)
    predictions = models['log_anomaly'].predict(scaled)
    probabilities = models['log_anomaly'].predict_proba(scaled)
    
    results = []
    for i, pred in enumerate(predictions):
        results.append({
            'anomaly_detected': bool(pred),
            'confidence': float(probabilities[i][pred]),
            'threat_level': 'high' if probabilities[i][1] > 0.8 else 'medium'
        })
    
    return jsonify({'results': results})

@app.route('/detect/text_anomaly', methods=['POST'])
def detect_text_anomaly():
    """
    POST /detect/text_anomaly
    Body: {"logs": ["log message 1", "log message 2"]}
    """
    data = request.json
    logs = data['logs']
    
    vectorized = preprocessors['text_anomaly'].transform(logs)
    predictions = models['text_anomaly'].predict(vectorized)
    probabilities = models['text_anomaly'].predict_proba(vectorized)
    
    results = []
    for i, (log, pred) in enumerate(zip(logs, predictions)):
        results.append({
            'log': log,
            'anomaly_detected': bool(pred),
            'confidence': float(probabilities[i][pred])
        })
    
    return jsonify({'results': results})

@app.route('/detect/insider_threat', methods=['POST'])
def detect_insider_threat():
    """
    POST /detect/insider_threat
    Body: {"features": [[39 behavioral features]]}
    """
    data = request.json
    features = np.array(data['features'])
    
    scaled = preprocessors['insider_threat'].transform(features)
    predictions = models['insider_threat'].predict(scaled)
    probabilities = models['insider_threat'].predict_proba(scaled)
    
    results = []
    for i, pred in enumerate(predictions):
        risk_score = float(probabilities[i][1]) * 100
        results.append({
            'threat_detected': bool(pred),
            'risk_score': risk_score,
            'risk_level': 'critical' if risk_score > 80 else 'high' if risk_score > 60 else 'medium',
            'action': 'investigate' if pred else 'monitor'
        })
    
    return jsonify({'results': results})

@app.route('/detect/web_attack', methods=['POST'])
def detect_web_attack():
    """
    POST /detect/web_attack
    Body: {"features": [[25 HTTP request features]]}
    """
    data = request.json
    features = np.array(data['features'])
    
    scaled = preprocessors['web_attack'].transform(features)
    predictions = models['web_attack'].predict(scaled)
    probabilities = models['web_attack'].predict_proba(scaled)
    
    results = []
    for i, pred in enumerate(predictions):
        results.append({
            'attack_detected': bool(pred),
            'confidence': float(probabilities[i][pred]),
            'action': 'block' if pred else 'allow',
            'attack_type': 'sqli_or_xss' if pred else None
        })
    
    return jsonify({'results': results})

if __name__ == '__main__':
    print("🚀 SOC ML Models API Server")
    print(f"   Models loaded: {len(models)}")
    print("   Starting server on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### Step 2: Run the API
```bash
python app.py
```

### Step 3: Test the API
```bash
# Health check
curl http://localhost:5000/health

# Test log anomaly detection
curl -X POST http://localhost:5000/detect/log_anomaly \
  -H "Content-Type: application/json" \
  -d '{"features": [[45,0,0,0,1,0,0,0,5,4624,0]]}'

# Test text anomaly detection
curl -X POST http://localhost:5000/detect/text_anomaly \
  -H "Content-Type: application/json" \
  -d '{"logs": ["ERROR: Authentication failed for user root"]}'
```

### Step 4: Deploy with Production Server
```bash
# Install production server
pip install gunicorn

# Run with gunicorn (4 workers)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 📊 OPTION 3: Integration with SIEM/SOC Platform

### Integration with Splunk
```python
# splunk_integration.py
import requests
from soc_models import SOCModels

soc_models = SOCModels('DEPLOY_READY_SOC_MODELS')

def analyze_splunk_event(event):
    """Analyze event from Splunk"""
    # Extract features from Splunk event
    features = extract_features(event)
    
    # Run through models
    prediction, probability = soc_models.detect_log_anomaly(features)
    
    if prediction[0] == 1:
        # Send alert back to Splunk
        send_splunk_alert(event, probability[0][1])
```

### Integration with ELK Stack
```python
# elk_integration.py
from elasticsearch import Elasticsearch
from soc_models import SOCModels

es = Elasticsearch(['localhost:9200'])
soc_models = SOCModels('DEPLOY_READY_SOC_MODELS')

def process_elk_logs():
    """Process logs from Elasticsearch"""
    logs = es.search(index='logs-*', body={'query': {'match_all': {}}})
    
    for log in logs['hits']['hits']:
        text = log['_source']['message']
        prediction, probability = soc_models.detect_text_anomaly([text])
        
        if prediction[0] == 1:
            # Index alert back to Elasticsearch
            es.index(index='security-alerts', body={
                'original_log': text,
                'confidence': probability[0][1],
                'timestamp': log['_source']['timestamp']
            })
```

---

## 🔒 SECURITY BEST PRACTICES

### 1. Model File Security
```bash
# Set appropriate permissions
chmod 600 *.pkl
chown app_user:app_group *.pkl
```

### 2. Input Validation
```python
def validate_features(features, expected_shape):
    """Validate input features"""
    if not isinstance(features, np.ndarray):
        raise ValueError("Features must be numpy array")
    if features.shape[1] != expected_shape:
        raise ValueError(f"Expected {expected_shape} features")
    if np.isnan(features).any():
        raise ValueError("Features contain NaN values")
    return True
```

### 3. Rate Limiting (for API)
```python
from flask_limiter import Limiter

limiter = Limiter(app, default_limits=["1000 per hour"])

@app.route('/detect/log_anomaly', methods=['POST'])
@limiter.limit("100 per minute")
def detect_log_anomaly():
    # ... detection logic
```

---

## 📈 MONITORING & MAINTENANCE

### 1. Log All Predictions
```python
import logging

logging.basicConfig(filename='model_predictions.log', level=logging.INFO)

def log_prediction(model_name, prediction, confidence):
    logging.info(f"{model_name}: pred={prediction}, conf={confidence:.3f}")
```

### 2. Track Performance Metrics
```python
from prometheus_client import Counter, Histogram

prediction_counter = Counter('predictions_total', 'Total predictions', ['model', 'result'])
inference_time = Histogram('inference_seconds', 'Inference time', ['model'])

@inference_time.labels('log_anomaly').time()
def detect_with_metrics(features):
    prediction, probability = model.predict(features)
    prediction_counter.labels('log_anomaly', 'anomaly' if prediction[0] else 'normal').inc()
    return prediction, probability
```

### 3. Model Retraining Schedule
- **Weekly:** Review false positives/negatives
- **Monthly:** Retrain models with new data
- **Quarterly:** Full model evaluation and update

---

## 🚨 ALERTING CONFIGURATION

### Example Alert Thresholds
```python
ALERT_CONFIG = {
    'log_anomaly': {
        'critical': 0.95,  # 95%+ confidence
        'high': 0.85,
        'medium': 0.70
    },
    'insider_threat': {
        'critical': 0.90,
        'high': 0.75,
        'medium': 0.60
    },
    'web_attack': {
        'critical': 0.98,  # Very high threshold to reduce false positives
        'high': 0.90,
        'medium': 0.80
    }
}

def send_alert(model_name, confidence, details):
    threshold = ALERT_CONFIG[model_name]
    
    if confidence >= threshold['critical']:
        # Page on-call engineer
        page_oncall(details)
    elif confidence >= threshold['high']:
        # Send email to SOC team
        email_soc_team(details)
    elif confidence >= threshold['medium']:
        # Log to SIEM for investigation
        log_to_siem(details)
```

---

## ✅ POST-DEPLOYMENT CHECKLIST

- [ ] Models loaded successfully
- [ ] API endpoints responding
- [ ] Logging configured
- [ ] Monitoring dashboards set up
- [ ] Alert routing configured
- [ ] Team trained on model outputs
- [ ] Incident response procedures updated
- [ ] Performance baseline established
- [ ] Backup and disaster recovery plan
- [ ] Documentation shared with team

---

## 🎯 PRODUCTION DEPLOYMENT TIMELINE

### Week 1: Testing
- Deploy to staging environment
- Run integration tests
- Performance testing
- Team training

### Week 2: Pilot
- Deploy to production (limited scope)
- Monitor closely
- Collect feedback
- Tune thresholds

### Week 3-4: Full Rollout
- Expand to full production
- Continuous monitoring
- Iterate based on feedback

---

## 📞 TROUBLESHOOTING

### Issue: Model loading fails
```python
# Solution: Check file paths and permissions
import os
print(os.listdir('DEPLOY_READY_SOC_MODELS'))
print(os.access('multi_os_log_anomaly_detector.pkl', os.R_OK))
```

### Issue: High latency
```python
# Solution: Batch predictions
predictions = model.predict(batch_features)  # Much faster than loop
```

### Issue: Memory usage too high
```python
# Solution: Load models on-demand or use model caching
from functools import lru_cache

@lru_cache(maxsize=1)
def get_model(model_name):
    return pickle.load(open(f'{model_name}.pkl', 'rb'))
```

---

**Deployment Guide Version:** 1.0  
**Last Updated:** October 12, 2025  
**Support:** See README.md for additional documentation


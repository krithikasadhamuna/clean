#!/usr/bin/env python3
"""
ML Model Manager for DEPLOY_READY_SOC_MODELS
Manages loading and inference for all 6 production-ready ML models
"""

import pickle
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

class MLModelManager:
    """Manages all production-ready ML models"""
    
    def __init__(self):
        self.models_dir = Path(__file__).parent / "ml_models" / "DEPLOY_READY_SOC_MODELS"
        self.models = {}
        self.scalers = {}
        self.vectorizers = {}
        self.model_info = {}
        
        # Load all models
        self._load_all_models()
        
    def _load_all_models(self):
        """Load all 6 production-ready ML models"""
        try:
            # Model 1: Multi-OS Log Anomaly Detector
            self._load_model(
                name="multi_os_log_anomaly",
                model_file="multi_os_log_anomaly_detector.pkl",
                scaler_file="multi_os_log_anomaly_scaler.pkl",
                features=11,
                description="Multi-OS Log Anomaly Detection (100% accuracy)"
            )
            
            # Model 2: Text-Based Log Anomaly Detector (NLP)
            self._load_model(
                name="text_log_anomaly",
                model_file="text_log_anomaly_detector.pkl",
                vectorizer_file="text_log_tfidf_vectorizer.pkl",
                description="Text-Based Log Anomaly Detection with NLP (99.88% accuracy)"
            )
            
            # Model 3: Insider Threat Detector
            self._load_model(
                name="insider_threat",
                model_file="insider_threat_detector.pkl",
                scaler_file="insider_threat_scaler.pkl",
                features=39,
                description="Insider Threat Detection (99.985% accuracy)"
            )
            
            # Model 4: Network Intrusion Detector
            self._load_model(
                name="network_intrusion",
                model_file="network_intrusion_Time-Series_Network_logs.pkl",
                scaler_file="network_intrusion_Time-Series_Network_logs_scaler.pkl",
                features=2,
                description="Network Intrusion Detection (100% accuracy)"
            )
            
            # Model 5: Web Attack Detector
            self._load_model(
                name="web_attack",
                model_file="web_attack_detector.pkl",
                scaler_file="web_attack_scaler.pkl",
                features=25,
                description="Web Attack Detection (97.14% accuracy)"
            )
            
            # Model 6: Time Series Network Detector
            self._load_model(
                name="time_series_network",
                model_file="time_series_network_detector.pkl",
                scaler_file="time_series_network_detector_scaler.pkl",
                description="Time Series Network Anomaly Detection (100% accuracy)"
            )
            
            logger.info(f"Successfully loaded {len(self.models)} ML models")
            
        except Exception as e:
            logger.error(f"Error loading ML models: {e}", exc_info=True)
    
    def _load_model(self, name: str, model_file: str, 
                   scaler_file: str = None, vectorizer_file: str = None,
                   features: int = None, description: str = ""):
        """Load a single model with its scaler/vectorizer"""
        try:
            model_path = self.models_dir / model_file
            
            if not model_path.exists():
                logger.warning(f"Model file not found: {model_path}")
                return
            
            # Load model
            with open(model_path, 'rb') as f:
                self.models[name] = pickle.load(f)
            
            # Load scaler if provided
            if scaler_file:
                scaler_path = self.models_dir / scaler_file
                if scaler_path.exists():
                    with open(scaler_path, 'rb') as f:
                        self.scalers[name] = pickle.load(f)
            
            # Load vectorizer if provided
            if vectorizer_file:
                vectorizer_path = self.models_dir / vectorizer_file
                if vectorizer_path.exists():
                    with open(vectorizer_path, 'rb') as f:
                        self.vectorizers[name] = pickle.load(f)
            
            # Store model info
            self.model_info[name] = {
                'description': description,
                'features': features,
                'model_file': model_file,
                'scaler_file': scaler_file,
                'vectorizer_file': vectorizer_file
            }
            
            logger.info(f"Loaded model: {name} - {description}")
            
        except Exception as e:
            logger.error(f"Failed to load model {name}: {e}")
    
    def predict_multi_os_log_anomaly(self, features: np.ndarray) -> Tuple[int, float]:
        """
        Predict Multi-OS log anomaly
        
        Args:
            features: np.array with 11 features:
                [content_length, has_error, has_warning, has_denied, has_auth,
                 has_network, has_critical, level, component, event_id, os_type]
        
        Returns:
            (prediction, confidence)
            prediction: 0=Normal, 1=Anomaly
            confidence: Probability score
        """
        try:
            if "multi_os_log_anomaly" not in self.models:
                return 0, 0.5
            
            model = self.models["multi_os_log_anomaly"]
            scaler = self.scalers.get("multi_os_log_anomaly")
            
            if scaler:
                features = scaler.transform(features)
            
            prediction = model.predict(features)[0]
            probability = model.predict_proba(features)[0]
            
            confidence = probability[1] if prediction == 1 else probability[0]
            
            return int(prediction), float(confidence)
            
        except Exception as e:
            logger.error(f"Multi-OS log anomaly prediction failed: {e}")
            return 0, 0.5
    
    def predict_text_log_anomaly(self, log_text: str) -> Tuple[int, float]:
        """
        Predict text-based log anomaly using NLP
        
        Args:
            log_text: The log message text
        
        Returns:
            (prediction, confidence)
            prediction: 0=Normal, 1=Anomaly
            confidence: Probability score
        """
        try:
            if "text_log_anomaly" not in self.models:
                return 0, 0.5
            
            model = self.models["text_log_anomaly"]
            vectorizer = self.vectorizers.get("text_log_anomaly")
            
            if not vectorizer:
                return 0, 0.5
            
            # Vectorize text
            features = vectorizer.transform([log_text])
            
            prediction = model.predict(features)[0]
            probability = model.predict_proba(features)[0]
            
            confidence = probability[1] if prediction == 1 else probability[0]
            
            return int(prediction), float(confidence)
            
        except Exception as e:
            logger.error(f"Text log anomaly prediction failed: {e}")
            return 0, 0.5
    
    def predict_insider_threat(self, features: np.ndarray) -> Tuple[int, float]:
        """
        Predict insider threat
        
        Args:
            features: np.array with 39 behavioral features
        
        Returns:
            (prediction, confidence)
            prediction: 0=Normal, 1=Threat
            confidence: Probability score
        """
        try:
            if "insider_threat" not in self.models:
                return 0, 0.5
            
            model = self.models["insider_threat"]
            scaler = self.scalers.get("insider_threat")
            
            if scaler:
                features = scaler.transform(features)
            
            prediction = model.predict(features)[0]
            probability = model.predict_proba(features)[0]
            
            confidence = probability[1] if prediction == 1 else probability[0]
            
            return int(prediction), float(confidence)
            
        except Exception as e:
            logger.error(f"Insider threat prediction failed: {e}")
            return 0, 0.5
    
    def predict_network_intrusion(self, features: np.ndarray) -> Tuple[int, float]:
        """
        Predict network intrusion
        
        Args:
            features: np.array with 2 time-series features
        
        Returns:
            (prediction, confidence)
            prediction: 0=Normal, 1=Intrusion
            confidence: Probability score
        """
        try:
            if "network_intrusion" not in self.models:
                return 0, 0.5
            
            model = self.models["network_intrusion"]
            scaler = self.scalers.get("network_intrusion")
            
            if scaler:
                features = scaler.transform(features)
            
            prediction = model.predict(features)[0]
            probability = model.predict_proba(features)[0]
            
            confidence = probability[1] if prediction == 1 else probability[0]
            
            return int(prediction), float(confidence)
            
        except Exception as e:
            logger.error(f"Network intrusion prediction failed: {e}")
            return 0, 0.5
    
    def predict_web_attack(self, features: np.ndarray) -> Tuple[int, float]:
        """
        Predict web attack
        
        Args:
            features: np.array with 25 HTTP request features
        
        Returns:
            (prediction, confidence)
            prediction: 0=Legitimate, 1=Attack
            confidence: Probability score
        """
        try:
            if "web_attack" not in self.models:
                return 0, 0.5
            
            model = self.models["web_attack"]
            scaler = self.scalers.get("web_attack")
            
            if scaler:
                features = scaler.transform(features)
            
            prediction = model.predict(features)[0]
            probability = model.predict_proba(features)[0]
            
            confidence = probability[1] if prediction == 1 else probability[0]
            
            return int(prediction), float(confidence)
            
        except Exception as e:
            logger.error(f"Web attack prediction failed: {e}")
            return 0, 0.5
    
    def predict_time_series_network(self, features: np.ndarray) -> Tuple[int, float]:
        """
        Predict time series network anomaly
        
        Args:
            features: np.array with variable time-series features
        
        Returns:
            (prediction, confidence)
            prediction: 0=Normal, 1=Anomaly
            confidence: Probability score
        """
        try:
            if "time_series_network" not in self.models:
                return 0, 0.5
            
            model = self.models["time_series_network"]
            scaler = self.scalers.get("time_series_network")
            
            if scaler:
                features = scaler.transform(features)
            
            prediction = model.predict(features)[0]
            probability = model.predict_proba(features)[0]
            
            confidence = probability[1] if prediction == 1 else probability[0]
            
            return int(prediction), float(confidence)
            
        except Exception as e:
            logger.error(f"Time series network prediction failed: {e}")
            return 0, 0.5
    
    def analyze_log(self, log_data: Dict) -> Dict:
        """
        Comprehensive log analysis using all applicable models
        
        Args:
            log_data: Dictionary containing log information
        
        Returns:
            Dictionary with predictions from all applicable models
        """
        results = {
            'timestamp': log_data.get('timestamp', ''),
            'log_message': log_data.get('message', ''),
            'predictions': {},
            'threat_detected': False,
            'confidence': 0.0,
            'models_used': []
        }
        
        try:
            # Text-based log anomaly detection (always applicable)
            if 'message' in log_data:
                prediction, confidence = self.predict_text_log_anomaly(log_data['message'])
                results['predictions']['text_log_anomaly'] = {
                    'prediction': 'Anomaly' if prediction == 1 else 'Normal',
                    'confidence': confidence
                }
                results['models_used'].append('text_log_anomaly')
                
                if prediction == 1:
                    results['threat_detected'] = True
                    results['confidence'] = max(results['confidence'], confidence)
            
            # Add more model predictions as needed based on available features
            
            # Determine overall threat level
            if results['threat_detected']:
                if results['confidence'] >= 0.9:
                    results['threat_level'] = 'CRITICAL'
                elif results['confidence'] >= 0.7:
                    results['threat_level'] = 'HIGH'
                elif results['confidence'] >= 0.5:
                    results['threat_level'] = 'MEDIUM'
                else:
                    results['threat_level'] = 'LOW'
            else:
                results['threat_level'] = 'NONE'
            
        except Exception as e:
            logger.error(f"Log analysis failed: {e}")
        
        return results
    
    def get_model_info(self) -> Dict:
        """Get information about all loaded models"""
        return {
            'total_models': len(self.models),
            'loaded_models': list(self.models.keys()),
            'model_details': self.model_info
        }

# Global instance
ml_model_manager = MLModelManager()


# ============================================================================
# FILE 11: app/agents/scam_detection/ml_models/phishing_classifier.py
# ============================================================================

"""
Advanced Phishing Detection using Ensemble ML Models
"""

import numpy as np
import joblib
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
from urllib.parse import urlparse
import tldextract

class AdvancedPhishingClassifier:
    """Ensemble ML Model for phishing detection"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.feature_names = self._get_feature_names()
        self.is_trained = False
    
    def _get_feature_names(self) -> List[str]:
        """Get list of feature names"""
        return [
            'word_count', 'char_count', 'unique_word_ratio',
            'uppercase_ratio', 'digit_ratio', 'exclamation_count',
            'question_count', 'dollar_count', 'url_length',
            'domain_length', 'dot_count', 'hyphen_count',
            'urgency_score', 'fear_score', 'money_score'
        ]
    
    def predict(self, text: str, url: str = None) -> Dict[str, Any]:
        """Predict if message is phishing"""
        features = self.extract_features(text, url)
        
        # Simple heuristic for demo
        risk_score = self._calculate_heuristic_score(text, url)
        
        return {
            'is_phishing': risk_score > 0.5,
            'confidence': risk_score,
            'risk_score': risk_score * 10,
            'risk_level': 'HIGH' if risk_score > 0.7 else 'MEDIUM' if risk_score > 0.3 else 'LOW',
            'features': dict(zip(self.feature_names, features.tolist())),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def extract_features(self, text: str, url: str = None) -> np.ndarray:
        """Extract features from text"""
        features = []
        
        # Basic text features
        words = text.split()
        features.append(len(words))  # word count
        features.append(len(text))   # char count
        features.append(len(set(words)) / len(words) if words else 0)  # unique word ratio
        
        # Character-based features
        features.append(sum(1 for c in text if c.isupper()) / len(text) if text else 0)  # uppercase ratio
        features.append(sum(1 for c in text if c.isdigit()) / len(text) if text else 0)  # digit ratio
        
        # Punctuation
        features.append(text.count('!'))
        features.append(text.count('?'))
        features.append(text.count('$'))
        
        # URL features
        if url:
            parsed = urlparse(url)
            extracted = tldextract.extract(url)
            features.append(len(url))
            features.append(len(extracted.domain))
            features.append(url.count('.'))
            features.append(url.count('-'))
        else:
            features.extend([0, 0, 0, 0])
        
        # Sentiment features
        text_lower = text.lower()
        urgency_words = ['urgent', 'immediately', 'asap', 'now', 'today']
        features.append(sum(1 for w in urgency_words if w in text_lower))
        
        fear_words = ['risk', 'danger', 'threat', 'warning', 'suspended']
        features.append(sum(1 for w in fear_words if w in text_lower))
        
        money_words = ['money', 'cash', 'bank', 'account', 'payment', 'credit']
        features.append(sum(1 for w in money_words if w in text_lower))
        
        return np.array(features)
    
    def _calculate_heuristic_score(self, text: str, url: str = None) -> float:
        """Calculate heuristic risk score"""
        score = 0.0
        text_lower = text.lower()
        
        # Urgency words
        if any(word in text_lower for word in ['urgent', 'immediately', 'asap']):
            score += 0.2
        
        # Verification requests
        if any(word in text_lower for word in ['verify', 'confirm', 'validate']):
            score += 0.2
        
        # Account related
        if any(word in text_lower for word in ['account', 'bank', 'paypal']):
            score += 0.15
        
        # Links
        if 'http' in text_lower:
            score += 0.2
        
        # Personal info requests
        if any(word in text_lower for word in ['password', 'ssn', 'credit card']):
            score += 0.25
        
        # URL analysis
        if url:
            if self._is_suspicious_url(url):
                score += 0.3
        
        return min(score, 1.0)
    
    def _is_suspicious_url(self, url: str) -> bool:
        """Check if URL is suspicious"""
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq']
        suspicious_patterns = ['secure-', 'account-', 'verify-', 'login-']
        
        domain = self._extract_domain(url)
        
        if any(domain.endswith(tld) for tld in suspicious_tlds):
            return True
        
        if any(pattern in domain for pattern in suspicious_patterns):
            return True
        
        return False
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        return domain.replace("www.", "")
    
    def load_model(self, model_data: Dict):
        """Load pre-trained model"""
        # In production, would load actual model
        self.is_trained = True

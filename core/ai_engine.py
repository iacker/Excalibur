from typing import Dict, List
import numpy as np
from sklearn.ensemble import RandomForestClassifier

class AIEngine:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        self.attack_patterns = {}
        self.vulnerability_database = {}
        
    def analyze_target(self, scan_results: Dict) -> List[Dict]:
        """Analyser les résultats du scan et suggérer des vecteurs d'attaque"""
        features = self._extract_features(scan_results)
        vulnerabilities = self._identify_vulnerabilities(scan_results)
        attack_vectors = self._generate_attack_vectors(features, vulnerabilities)
        return self._prioritize_attacks(attack_vectors)
    
    def _extract_features(self, scan_results: Dict) -> np.ndarray:
        """Extraire les caractéristiques pertinentes des résultats du scan"""
        features = []
        for port, info in scan_results.get('ports', {}).items():
            feature_vector = [
                int(port),
                self._service_risk_score(info.get('service', '')),
                self._version_vulnerability_score(info.get('version', '')),
                len(info.get('scripts', [])),
            ]
            features.append(feature_vector)
        return np.array(features)
    
    def _identify_vulnerabilities(self, scan_results: Dict) -> List[Dict]:
        """Identifier les vulnérabilités potentielles"""
        vulnerabilities = []
        for port, info in scan_results.get('ports', {}).items():
            service = info.get('service', '')
            version = info.get('version', '')
            vulns = self.vulnerability_database.get(f"{service}_{version}", [])
            vulnerabilities.extend(vulns)
        return vulnerabilities
    
    def _generate_attack_vectors(self, features: np.ndarray, vulnerabilities: List[Dict]) -> List[Dict]:
        """Générer des vecteurs d'attaque basés sur les caractéristiques et vulnérabilités"""
        attack_vectors = []
        predictions = self.model.predict_proba(features)
        
        for prediction, vulnerability in zip(predictions, vulnerabilities):
            attack_vector = {
                'vulnerability': vulnerability,
                'success_probability': float(np.max(prediction)),
                'technique': self._select_technique(vulnerability),
                'priority': self._calculate_priority(prediction, vulnerability)
            }
            attack_vectors.append(attack_vector)
        
        return attack_vectors
    
    def _prioritize_attacks(self, attack_vectors: List[Dict]) -> List[Dict]:
        """Prioriser les vecteurs d'attaque"""
        return sorted(attack_vectors, key=lambda x: x['priority'], reverse=True)
    
    def _service_risk_score(self, service: str) -> float:
        """Calculer le score de risque pour un service donné"""
        risk_scores = {
            'http': 0.8,
            'https': 0.7,
            'ftp': 0.6,
            'ssh': 0.5,
            'smb': 0.9
        }
        return risk_scores.get(service.lower(), 0.3)
    
    def _version_vulnerability_score(self, version: str) -> float:
        """Calculer le score de vulnérabilité basé sur la version"""
        try:
            ver_parts = version.split('.')
            if len(ver_parts) >= 2:
                return 1.0 - (float(ver_parts[0]) * 0.1)
        except:
            pass
        return 0.5
    
    def _select_technique(self, vulnerability: Dict) -> str:
        """Sélectionner la technique d'attaque appropriée"""
        techniques = {
            'rce': 'exploit/rce',
            'sqli': 'exploit/sql_injection',
            'xss': 'exploit/xss',
            'buffer_overflow': 'exploit/buffer_overflow'
        }
        return techniques.get(vulnerability.get('type'), 'exploit/generic')
    
    def _calculate_priority(self, prediction: np.ndarray, vulnerability: Dict) -> float:
        """Calculer la priorité d'attaque"""
        impact = vulnerability.get('impact', 5.0) / 10.0
        probability = float(np.max(prediction))
        return (impact + probability) / 2
    
    def update_model(self, attack_result: Dict):
        """Mettre à jour le modèle avec les résultats d'attaque"""
        if 'success' in attack_result and 'features' in attack_result:
            X = np.array([attack_result['features']])
            y = np.array([attack_result['success']])
            self.model.fit(X, y)

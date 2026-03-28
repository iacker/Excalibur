from typing import Dict, List, Optional
from enum import Enum
import json
import yaml
import logging

class FormationType(Enum):
    TESTUDO = "testudo"           # Formation défensive maximale
    CUNEUS = "cuneus"            # Formation d'attaque en coin
    REPLEGARE = "replegare"      # Repli stratégique
    ORBIS = "orbis"              # Formation circulaire défensive

class TurtlePhase(Enum):
    RECONNAISSANCE = "reconnaissance"
    FORTIFICATION = "fortification"
    PROBE = "probe"
    ADVANCE = "advance"
    SECURE = "secure"
    CONSOLIDATE = "consolidate"

class RomanTurtle:
    def __init__(self):
        self.current_formation: FormationType = FormationType.TESTUDO
        self.current_phase: TurtlePhase = TurtlePhase.RECONNAISSANCE
        self.secured_positions: List[str] = []
        self.threat_map: Dict[str, float] = {}
        self.logger = logging.getLogger("RomanTurtle")

    def analyze_battlefield(self, scan_results: Dict) -> Dict:
        """Analyser les résultats du scan comme un général romain analysant le terrain"""
        threats = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': []
        }
        
        for service, details in scan_results.items():
            risk_level = self._evaluate_threat_level(details)
            position = {'service': service, 'details': details}
            
            if risk_level > 0.7:
                threats['high_risk'].append(position)
            elif risk_level > 0.4:
                threats['medium_risk'].append(position)
            else:
                threats['low_risk'].append(position)
                
        return threats

    def generate_formation_plan(self, threats: Dict) -> List[Dict]:
        """Générer un plan d'attaque basé sur la formation de la tortue romaine"""
        plan = []
        
        # Phase 1: Reconnaissance (Exploratores)
        plan.append({
            'phase': 'reconnaissance',
            'formation': FormationType.TESTUDO,
            'actions': self._generate_recon_actions(threats['low_risk'])
        })
        
        # Phase 2: Sécurisation initiale
        plan.append({
            'phase': 'fortification',
            'formation': FormationType.ORBIS,
            'actions': self._generate_fortification_actions(threats['low_risk'])
        })
        
        # Phase 3: Progression méthodique
        for position in threats['medium_risk']:
            plan.append({
                'phase': 'advance',
                'formation': FormationType.CUNEUS,
                'actions': self._generate_advance_actions(position)
            })
            plan.append({
                'phase': 'secure',
                'formation': FormationType.TESTUDO,
                'actions': self._generate_secure_actions(position)
            })
        
        return plan

    def generate_ansible_playbook(self, plan: List[Dict]) -> str:
        """Générer un playbook Ansible basé sur le plan d'attaque"""
        playbook = []
        
        for phase in plan:
            task_name = f"Phase: {phase['phase']} - Formation: {phase['formation'].value}"
            tasks = []
            
            for action in phase['actions']:
                tasks.append({
                    'name': action['description'],
                    'ansible.builtin.shell': action['command'],
                    'register': f"result_{action['id']}",
                    'ignore_errors': True
                })
                
                # Ajouter une tâche de vérification de sécurité après chaque action
                tasks.append({
                    'name': f"Security check after {action['description']}",
                    'ansible.builtin.shell': self._generate_security_check(action),
                    'register': 'security_check'
                })
                
                # Ajouter une condition de repli si nécessaire
                tasks.append({
                    'name': 'Tactical retreat if needed',
                    'ansible.builtin.shell': 'echo "Initiating tactical retreat"',
                    'when': 'security_check.rc != 0'
                })
            
            playbook.append({
                'name': task_name,
                'hosts': 'target',
                'tasks': tasks
            })
        
        return yaml.dump(playbook, default_flow_style=False)

    def _evaluate_threat_level(self, details: Dict) -> float:
        """Évaluer le niveau de menace d'un service"""
        threat_score = 0.0
        
        # Évaluer les ports standards vs non-standards
        if details.get('port') in [80, 443, 22, 21]:
            threat_score += 0.3
        else:
            threat_score += 0.6
            
        # Évaluer la présence de versions vulnérables
        if details.get('version') and 'outdated' in details.get('version_info', []):
            threat_score += 0.4
            
        # Évaluer les bannières et signatures
        if details.get('banner'):
            if any(risk in details['banner'].lower() for risk in ['admin', 'root', 'system']):
                threat_score += 0.3
                
        return min(1.0, threat_score)

    def _generate_recon_actions(self, positions: List[Dict]) -> List[Dict]:
        """Générer des actions de reconnaissance passive"""
        actions = []
        for pos in positions:
            actions.extend([
                {
                    'id': f"recon_{pos['service']}",
                    'description': f"Passive reconnaissance of {pos['service']}",
                    'command': f"nmap -sS -sV -Pn {pos['service']}",
                    'cleanup': "rm -f /tmp/scan_*"
                },
                {
                    'id': f"service_enum_{pos['service']}",
                    'description': f"Service enumeration for {pos['service']}",
                    'command': f"enum4linux -a {pos['service']}",
                    'cleanup': "rm -f /tmp/enum_*"
                }
            ])
        return actions

    def _generate_fortification_actions(self, positions: List[Dict]) -> List[Dict]:
        """Générer des actions pour sécuriser une position"""
        actions = []
        for pos in positions:
            actions.extend([
                {
                    'id': f"secure_{pos['service']}",
                    'description': f"Establish secure position at {pos['service']}",
                    'command': f"nmap --script safe {pos['service']}",
                    'cleanup': f"rm -f /tmp/secure_{pos['service']}_*"
                }
            ])
        return actions

    def _generate_advance_actions(self, position: Dict) -> List[Dict]:
        """Générer des actions pour une avance prudente"""
        return [{
            'id': f"advance_{position['service']}",
            'description': f"Advance towards {position['service']}",
            'command': self._get_advance_command(position),
            'cleanup': f"rm -f /tmp/advance_{position['service']}_*"
        }]

    def _generate_secure_actions(self, position: Dict) -> List[Dict]:
        """Générer des actions pour sécuriser une nouvelle position"""
        return [{
            'id': f"hold_{position['service']}",
            'description': f"Secure position at {position['service']}",
            'command': f"nmap --script vuln {position['service']}",
            'cleanup': f"rm -f /tmp/hold_{position['service']}_*"
        }]

    def _get_advance_command(self, position: Dict) -> str:
        """Obtenir la commande appropriée pour avancer vers une position"""
        service_type = position['service']
        if 'http' in service_type:
            return f"nikto -h {position['details']['host']}"
        elif 'smb' in service_type:
            return f"smbmap -H {position['details']['host']}"
        else:
            return f"nmap -sV -A {position['details']['host']}"

    def _generate_security_check(self, action: Dict) -> str:
        """Générer une commande de vérification de sécurité"""
        return f"nmap -sS -p- --max-rate 100 {action['target']} -oX /tmp/security_check_{action['id']}.xml"

    def update_threat_map(self, scan_result: Dict):
        """Mettre à jour la carte des menaces"""
        for service, details in scan_result.items():
            self.threat_map[service] = self._evaluate_threat_level(details)

    def suggest_formation_change(self, current_threats: Dict) -> FormationType:
        """Suggérer un changement de formation basé sur les menaces actuelles"""
        high_risk_count = len(current_threats['high_risk'])
        medium_risk_count = len(current_threats['medium_risk'])
        
        if high_risk_count > 2:
            return FormationType.TESTUDO
        elif medium_risk_count > high_risk_count:
            return FormationType.CUNEUS
        elif high_risk_count == 0:
            return FormationType.ORBIS
        else:
            return FormationType.REPLEGARE
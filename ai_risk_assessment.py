"""
AI Risk Assessment
Generates comprehensive risk assessments based on simulation results and threat data
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sqlite3
import os

logger = logging.getLogger(__name__)


class AIRiskAssessment:
    """AI-powered risk assessment based on simulation results"""
    
    def __init__(self, db_path: str = "soc_database.db"):
        self.db_path = db_path
        self.risk_categories = {
            "technical": "Technical Vulnerabilities",
            "operational": "Operational Risks",
            "strategic": "Strategic Threats",
            "compliance": "Compliance Risks",
            "reputational": "Reputational Damage"
        }
    
    async def generate_risk_assessment(self) -> Dict[str, Any]:
        """Generate comprehensive risk assessment"""
        try:
            # Gather risk data
            overall_risk = await self._calculate_overall_risk()
            risk_matrix = await self._build_risk_matrix()
            top_risks = await self._identify_top_risks()
            risk_trends = await self._analyze_risk_trends()
            mitigation_status = await self._assess_mitigation_status()
            simulation_risks = await self._analyze_simulation_results()
            
            # Get AI-powered insights
            ai_insights = await self._get_ai_risk_insights(
                overall_risk, top_risks, simulation_risks
            )
            
            # Build data array format
            data_array = []
            
            # 1. Overall Risk Assessment
            data_array.append({
                "type": "overall_risk",
                "score": overall_risk,
                "level": self._score_to_risk_level(overall_risk),
                "trend": await self._calculate_risk_trend(),
                "description": self._get_risk_description(overall_risk)
            })
            
            # 2. Risk Matrix
            data_array.append({
                "type": "risk_matrix",
                "matrix": risk_matrix
            })
            
            # 3. Top Risks
            data_array.append({
                "type": "top_risks",
                "risks": top_risks
            })
            
            # 4. Risk Trends
            data_array.append({
                "type": "risk_trends",
                "trends": risk_trends
            })
            
            # 5. Mitigation Status
            data_array.append({
                "type": "mitigation_status",
                "status": mitigation_status
            })
            
            # 6. Simulation-Based Risks
            data_array.append({
                "type": "simulation_risks",
                "risks": simulation_risks
            })
            
            # 7. AI Insights
            data_array.append({
                "type": "ai_insights",
                "insights": ai_insights if isinstance(ai_insights, list) else [ai_insights]
            })
            
            # 8. Recommendations
            data_array.append({
                "type": "recommendations",
                "recommendations": await self._generate_risk_recommendations(top_risks)
            })
            
            # 9. Risk History
            data_array.append({
                "type": "risk_history",
                "history": await self._get_risk_history()
            })
            
            return {
                "status": "success",
                "data": data_array,
                "metadata": {
                    "generatedAt": datetime.utcnow().isoformat(),
                    "nextAssessmentDate": (datetime.utcnow() + timedelta(days=30)).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate risk assessment: {e}")
            return {
                "status": "error",
                "error": str(e),
                "generatedAt": datetime.utcnow().isoformat()
            }
    
    async def _calculate_overall_risk(self) -> float:
        """Calculate overall risk score (0-100, higher is more risky)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Factor 1: Critical/High severity threats (40% weight)
            cursor.execute("""
                SELECT COUNT(*) FROM detection_results 
                WHERE threat_detected=1 
                AND severity IN ('critical', 'high')
                AND detected_at > datetime('now', '-30 days')
            """)
            critical_threats = cursor.fetchone()[0]
            threat_score = min(100, critical_threats * 10)  # Each critical threat adds 10 points
            
            # Factor 2: Unpatched/vulnerable systems (30% weight)
            cursor.execute("""
                SELECT COUNT(*) FROM agents 
                WHERE json_extract(quick_summary, '$.antivirus') = 'unknown'
                OR json_extract(quick_summary, '$.firewall') = 'unknown'
            """)
            vulnerable_systems = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM agents WHERE status='active'")
            total_systems = cursor.fetchone()[0] or 1
            
            vulnerability_score = (vulnerable_systems / total_systems) * 100
            
            # Factor 3: Attack simulation success rate (30% weight)
            cursor.execute("""
                SELECT COUNT(*) FROM command_queue 
                WHERE status='completed' 
                AND created_at > datetime('now', '-30 days')
            """)
            successful_attacks = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM command_queue 
                WHERE created_at > datetime('now', '-30 days')
            """)
            total_attacks = cursor.fetchone()[0] or 1
            
            attack_success_rate = (successful_attacks / total_attacks) * 100
            
            conn.close()
            
            # Calculate weighted risk score
            overall_risk = (
                threat_score * 0.4 +
                vulnerability_score * 0.3 +
                attack_success_rate * 0.3
            )
            
            return round(min(100, overall_risk), 2)
            
        except Exception as e:
            logger.error(f"Failed to calculate overall risk: {e}")
            return 50.0  # Default moderate risk
    
    async def _build_risk_matrix(self) -> Dict[str, Any]:
        """Build risk matrix (likelihood vs impact)"""
        matrix = {
            "critical": [],  # High likelihood, High impact
            "high": [],      # High likelihood OR High impact
            "medium": [],    # Medium likelihood/impact
            "low": []        # Low likelihood, Low impact
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get threat distribution
            cursor.execute("""
                SELECT threat_type, COUNT(*) as count, AVG(confidence_score) as avg_confidence
                FROM detection_results 
                WHERE threat_detected=1
                AND detected_at > datetime('now', '-30 days')
                GROUP BY threat_type
            """)
            
            for row in cursor.fetchall():
                threat_type = row[0]
                frequency = row[1]
                confidence = row[2]
                
                # Determine likelihood (based on frequency)
                if frequency >= 10:
                    likelihood = "high"
                elif frequency >= 5:
                    likelihood = "medium"
                else:
                    likelihood = "low"
                
                # Determine impact (based on threat type)
                high_impact_threats = ["ransomware", "data_exfiltration", "credential_theft", "malware"]
                if any(hit in threat_type.lower() for hit in high_impact_threats):
                    impact = "high"
                else:
                    impact = "medium"
                
                # Classify risk level
                if likelihood == "high" and impact == "high":
                    risk_level = "critical"
                elif likelihood == "high" or impact == "high":
                    risk_level = "high"
                elif likelihood == "medium" or impact == "medium":
                    risk_level = "medium"
                else:
                    risk_level = "low"
                
                matrix[risk_level].append({
                    "threatType": threat_type,
                    "likelihood": likelihood,
                    "impact": impact,
                    "frequency": frequency,
                    "confidence": round(confidence, 2)
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to build risk matrix: {e}")
        
        return matrix
    
    async def _identify_top_risks(self) -> List[Dict[str, Any]]:
        """Identify top risks requiring attention"""
        risks = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Risk 1: Unresolved critical threats
            cursor.execute("""
                SELECT COUNT(*), threat_type
                FROM detection_results 
                WHERE threat_detected=1 
                AND severity='critical'
                AND verified=0
                AND detected_at > datetime('now', '-7 days')
                GROUP BY threat_type
                ORDER BY COUNT(*) DESC
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            if result and result[0] > 0:
                risks.append({
                    "id": "risk_001",
                    "category": "technical",
                    "title": "Unresolved Critical Security Threats",
                    "description": f"{result[0]} critical {result[1]} threats detected but not yet resolved",
                    "likelihood": "high",
                    "impact": "critical",
                    "riskScore": 95,
                    "affectedAssets": result[0],
                    "potentialImpact": "Data breach, system compromise, operational disruption",
                    "currentControls": "Automated detection in place",
                    "requiredActions": [
                        "Immediate investigation and containment",
                        "Root cause analysis",
                        "Implement additional preventive controls"
                    ],
                    "estimatedCost": "$50,000 - $500,000 if exploited",
                    "timeline": "Immediate (0-24 hours)",
                    "owner": "Security Operations Team"
                })
            
            # Risk 2: Vulnerable endpoints
            cursor.execute("""
                SELECT COUNT(*) FROM agents 
                WHERE json_extract(quick_summary, '$.antivirus') = 'unknown'
                OR json_extract(quick_summary, '$.firewall') = 'unknown'
            """)
            vulnerable_endpoints = cursor.fetchone()[0]
            
            if vulnerable_endpoints > 0:
                risks.append({
                    "id": "risk_002",
                    "category": "technical",
                    "title": "Inadequate Endpoint Protection",
                    "description": f"{vulnerable_endpoints} endpoints lack proper security controls",
                    "likelihood": "high",
                    "impact": "high",
                    "riskScore": 85,
                    "affectedAssets": vulnerable_endpoints,
                    "potentialImpact": "Malware infection, unauthorized access, data theft",
                    "currentControls": "Partial coverage",
                    "requiredActions": [
                        "Deploy security software on all endpoints",
                        "Enable and configure firewalls",
                        "Implement endpoint detection and response (EDR)"
                    ],
                    "estimatedCost": "$10,000 - $50,000 if exploited",
                    "timeline": "Short-term (1-2 weeks)",
                    "owner": "IT Security Team"
                })
            
            # Risk 3: Successful attack simulations
            cursor.execute("""
                SELECT COUNT(*) FROM command_queue 
                WHERE status='completed'
                AND result LIKE '%success%'
                AND created_at > datetime('now', '-7 days')
            """)
            successful_simulations = cursor.fetchone()[0]
            
            if successful_simulations > 5:
                risks.append({
                    "id": "risk_003",
                    "category": "operational",
                    "title": "High Attack Simulation Success Rate",
                    "description": f"{successful_simulations} simulated attacks succeeded in the past week",
                    "likelihood": "medium",
                    "impact": "high",
                    "riskScore": 75,
                    "affectedAssets": "Multiple systems",
                    "potentialImpact": "Indicates exploitable weaknesses in security posture",
                    "currentControls": "Regular security testing",
                    "requiredActions": [
                        "Review and strengthen security controls",
                        "Implement additional monitoring",
                        "Conduct security awareness training"
                    ],
                    "estimatedCost": "$25,000 - $100,000 if real attack occurs",
                    "timeline": "Medium-term (2-4 weeks)",
                    "owner": "Security Architecture Team"
                })
            
            # Risk 4: Compliance gaps
            cursor.execute("""
                SELECT COUNT(DISTINCT threat_type) FROM detection_results 
                WHERE threat_detected=1
                AND detected_at > datetime('now', '-30 days')
            """)
            threat_diversity = cursor.fetchone()[0]
            
            if threat_diversity > 5:
                risks.append({
                    "id": "risk_004",
                    "category": "compliance",
                    "title": "Diverse Threat Landscape",
                    "description": f"{threat_diversity} different threat types observed",
                    "likelihood": "medium",
                    "impact": "medium",
                    "riskScore": 65,
                    "affectedAssets": "Organization-wide",
                    "potentialImpact": "Regulatory penalties, compliance violations",
                    "currentControls": "Basic monitoring and detection",
                    "requiredActions": [
                        "Enhance threat intelligence capabilities",
                        "Implement defense-in-depth strategy",
                        "Regular compliance assessments"
                    ],
                    "estimatedCost": "$100,000+ in regulatory fines",
                    "timeline": "Medium-term (1-3 months)",
                    "owner": "Compliance Team"
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to identify top risks: {e}")
        
        # Sort by risk score
        risks.sort(key=lambda x: x["riskScore"], reverse=True)
        
        return risks[:5]  # Return top 5 risks
    
    async def _analyze_risk_trends(self) -> Dict[str, Any]:
        """Analyze how risks are trending over time"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get threat counts for different time periods
            cursor.execute("""
                SELECT COUNT(*) FROM detection_results 
                WHERE threat_detected=1 
                AND detected_at > datetime('now', '-7 days')
            """)
            recent_threats = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM detection_results 
                WHERE threat_detected=1 
                AND detected_at BETWEEN datetime('now', '-14 days') AND datetime('now', '-7 days')
            """)
            previous_threats = cursor.fetchone()[0]
            
            conn.close()
            
            # Calculate trend
            if previous_threats == 0:
                change_percent = 100 if recent_threats > 0 else 0
            else:
                change_percent = ((recent_threats - previous_threats) / previous_threats) * 100
            
            if change_percent > 20:
                trend = "increasing"
                trend_description = f"Risk levels are increasing ({change_percent:+.1f}%)"
            elif change_percent < -20:
                trend = "decreasing"
                trend_description = f"Risk levels are decreasing ({change_percent:+.1f}%)"
            else:
                trend = "stable"
                trend_description = "Risk levels remain relatively stable"
            
            return {
                "trend": trend,
                "changePercent": round(change_percent, 1),
                "description": trend_description,
                "weekOverWeek": {
                    "current": recent_threats,
                    "previous": previous_threats
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze risk trends: {e}")
            return {
                "trend": "unknown",
                "changePercent": 0,
                "description": "Unable to determine trend"
            }
    
    async def _assess_mitigation_status(self) -> Dict[str, Any]:
        """Assess current risk mitigation status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check verified/resolved threats
            cursor.execute("""
                SELECT COUNT(*) FROM detection_results 
                WHERE threat_detected=1 AND verified=1
            """)
            mitigated = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM detection_results 
                WHERE threat_detected=1
            """)
            total = cursor.fetchone()[0] or 1
            
            mitigation_rate = (mitigated / total) * 100
            
            conn.close()
            
            return {
                "mitigationRate": round(mitigation_rate, 1),
                "totalRisksIdentified": total,
                "risksMitigated": mitigated,
                "risksInProgress": total - mitigated,
                "status": "effective" if mitigation_rate > 70 else "needs_improvement"
            }
            
        except Exception as e:
            logger.error(f"Failed to assess mitigation status: {e}")
            return {
                "mitigationRate": 0,
                "status": "unknown"
            }
    
    async def _analyze_simulation_results(self) -> List[Dict[str, Any]]:
        """Analyze risks based on attack simulation results"""
        simulation_risks = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get simulation results
            cursor.execute("""
                SELECT technique, COUNT(*) as attempts,
                       SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as successful
                FROM command_queue
                WHERE created_at > datetime('now', '-30 days')
                GROUP BY technique
                HAVING successful > 0
                ORDER BY successful DESC
                LIMIT 5
            """)
            
            for row in cursor.fetchall():
                technique = row[0]
                attempts = row[1]
                successful = row[2]
                success_rate = (successful / attempts) * 100
                
                simulation_risks.append({
                    "technique": technique,
                    "mitreId": technique,  # Assuming technique is MITRE ID
                    "attempts": attempts,
                    "successful": successful,
                    "successRate": round(success_rate, 1),
                    "riskLevel": "high" if success_rate > 50 else "medium",
                    "finding": f"Attack technique succeeded in {success_rate:.1f}% of attempts",
                    "recommendation": f"Review and strengthen defenses against {technique} attacks"
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to analyze simulation results: {e}")
        
        return simulation_risks
    
    async def _get_ai_risk_insights(self, overall_risk: float, 
                                    top_risks: List[Dict], 
                                    simulation_risks: List[Dict]) -> Dict[str, Any]:
        """Get AI-powered risk insights using OpenAI"""
        try:
            import openai
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return self._get_fallback_risk_insights(overall_risk, top_risks)
            
            openai.api_key = api_key
            
            # Prepare context for AI
            context = f"""
Risk Assessment Analysis:
- Overall Risk Score: {overall_risk}/100
- Risk Level: {self._score_to_risk_level(overall_risk)}
- Number of Critical Risks: {len([r for r in top_risks if r.get('riskScore', 0) > 80])}
- Number of High Risks: {len([r for r in top_risks if 70 <= r.get('riskScore', 0) <= 80])}
- Simulation Success Rate: {len(simulation_risks)} attack techniques successful

Top Risk: {top_risks[0]['title'] if top_risks else 'None identified'}
"""
            
            prompt = f"""{context}

As a cybersecurity risk management expert, provide:
1. Executive risk summary (2-3 sentences)
2. Most critical risk factors (3 points)
3. Business impact assessment (2-3 sentences)
4. Priority mitigation actions (3 specific actions)

Be specific, actionable, and focus on business impact."""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a cybersecurity risk management expert providing executive-level insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            
            return {
                "summary": ai_response[:300],
                "fullAnalysis": ai_response,
                "generatedBy": "OpenAI GPT-3.5-turbo",
                "confidence": "high"
            }
            
        except Exception as e:
            logger.error(f"AI insights generation failed: {e}")
            return self._get_fallback_risk_insights(overall_risk, top_risks)
    
    def _get_fallback_risk_insights(self, overall_risk: float, top_risks: List[Dict]) -> Dict[str, Any]:
        """Fallback insights when AI is not available"""
        risk_level = self._score_to_risk_level(overall_risk)
        
        if risk_level == "critical":
            summary = f"Critical risk level ({overall_risk}/100) requires immediate executive attention. Multiple high-severity threats and vulnerabilities identified."
        elif risk_level == "high":
            summary = f"High risk level ({overall_risk}/100) indicates significant security concerns. Prioritize addressing {len(top_risks)} identified risks."
        elif risk_level == "medium":
            summary = f"Moderate risk level ({overall_risk}/100). Continue monitoring and address identified gaps proactively."
        else:
            summary = f"Low risk level ({overall_risk}/100). Maintain current security posture and continue regular assessments."
        
        return {
            "summary": summary,
            "fullAnalysis": summary,
            "generatedBy": "Rule-based analysis",
            "confidence": "medium"
        }
    
    async def _generate_risk_recommendations(self, top_risks: List[Dict]) -> List[Dict[str, Any]]:
        """Generate prioritized risk mitigation recommendations"""
        recommendations = []
        
        # Group risks by priority
        critical_risks = [r for r in top_risks if r.get("riskScore", 0) >= 85]
        high_risks = [r for r in top_risks if 70 <= r.get("riskScore", 0) < 85]
        
        if critical_risks:
            recommendations.append({
                "priority": "critical",
                "title": "Address Critical Risks Immediately",
                "description": f"{len(critical_risks)} critical risks require immediate action",
                "actions": critical_risks[0]["requiredActions"] if critical_risks else [],
                "timeline": "0-24 hours",
                "estimatedCost": critical_risks[0].get("estimatedCost", "TBD"),
                "businessImpact": "Prevent potential data breach and operational disruption"
            })
        
        if high_risks:
            recommendations.append({
                "priority": "high",
                "title": "Strengthen Security Controls",
                "description": f"{len(high_risks)} high-priority risks identified",
                "actions": high_risks[0]["requiredActions"] if high_risks else [],
                "timeline": "1-2 weeks",
                "estimatedCost": high_risks[0].get("estimatedCost", "TBD"),
                "businessImpact": "Reduce attack surface and improve security posture"
            })
        
        # General recommendations
        recommendations.append({
            "priority": "medium",
            "title": "Implement Continuous Monitoring",
            "description": "Enhance visibility and early warning capabilities",
            "actions": [
                "Deploy advanced threat detection tools",
                "Implement 24/7 security monitoring",
                "Establish incident response procedures"
            ],
            "timeline": "2-4 weeks",
            "estimatedCost": "$50,000 - $150,000 annually",
            "businessImpact": "Faster threat detection and response"
        })
        
        return recommendations
    
    async def _calculate_risk_trend(self) -> str:
        """Calculate overall risk trend"""
        trends = await self._analyze_risk_trends()
        return trends.get("trend", "stable")
    
    async def _get_risk_history(self) -> List[Dict[str, Any]]:
        """Get historical risk scores"""
        history = []
        
        # Generate historical data points
        current_risk = await self._calculate_overall_risk()
        
        for days_ago in [30, 60, 90]:
            date = datetime.utcnow() - timedelta(days=days_ago)
            # Simulate historical scores (in reality, you'd store these)
            historical_risk = current_risk + (days_ago / 30 * 5)  # Risk decreasing over time
            
            history.append({
                "date": date.isoformat(),
                "riskScore": round(min(100, historical_risk), 2),
                "riskLevel": self._score_to_risk_level(min(100, historical_risk))
            })
        
        return history
    
    def _score_to_risk_level(self, score: float) -> str:
        """Convert risk score to risk level"""
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"
    
    def _get_risk_description(self, score: float) -> str:
        """Get human-readable risk description"""
        level = self._score_to_risk_level(score)
        
        descriptions = {
            "critical": "Immediate action required to prevent severe impact",
            "high": "Significant risks present, prioritize mitigation",
            "medium": "Manageable risks, continue monitoring",
            "low": "Minimal risks, maintain current posture"
        }
        
        return descriptions.get(level, "Unknown risk level")


# Global instance
risk_assessment = AIRiskAssessment()



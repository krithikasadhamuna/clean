"""
Professional PDF Report Generator
Generates professional PDF reports for security professionals
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus import Image, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF

logger = logging.getLogger(__name__)


class ProfessionalPDFGenerator:
    """Generates professional PDF reports for security professionals"""
    
    def __init__(self, output_dir: str = "server/downloads"):
        self.output_dir = output_dir
        self.ensure_output_dir()
        
        # Professional color scheme
        self.colors = {
            'primary': colors.HexColor('#1f4e79'),      # Dark blue
            'secondary': colors.HexColor('#2e7d32'),    # Green
            'accent': colors.HexColor('#d32f2f'),       # Red
            'warning': colors.HexColor('#f57c00'),      # Orange
            'text': colors.HexColor('#212121'),         # Dark gray
            'light_gray': colors.HexColor('#f5f5f5'),   # Light gray
            'border': colors.HexColor('#e0e0e0')        # Border gray
        }
        
        # Setup styles
        self.setup_styles()
    
    def ensure_output_dir(self):
        """Ensure output directory exists"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def setup_styles(self):
        """Setup professional document styles"""
        self.styles = getSampleStyleSheet()
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=self.colors['primary'],
            fontName='Helvetica-Bold'
        ))
        
        # Heading 1 style
        self.styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=self.colors['primary'],
            fontName='Helvetica-Bold'
        ))
        
        # Heading 2 style
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=self.colors['secondary'],
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=self.colors['text'],
            fontName='Helvetica'
        ))
        
        # Executive summary style
        self.styles.add(ParagraphStyle(
            name='ExecutiveSummary',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            textColor=self.colors['text'],
            fontName='Helvetica',
            alignment=TA_JUSTIFY,
            leftIndent=20,
            rightIndent=20
        ))
    
    def generate_risk_assessment_pdf(self, report_data: Dict[str, Any]) -> str:
        """Generate professional Risk Assessment PDF report"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Risk_Assessment_Report_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            story = []
            
            # Cover page
            story.extend(self._create_cover_page("Risk Assessment Report", report_data))
            story.append(PageBreak())
            
            # Executive summary
            story.extend(self._create_executive_summary(report_data))
            story.append(PageBreak())
            
            # Risk overview
            story.extend(self._create_risk_overview(report_data))
            story.append(PageBreak())
            
            # Asset inventory
            story.extend(self._create_asset_inventory(report_data))
            story.append(PageBreak())
            
            # User access review
            story.extend(self._create_user_access_review(report_data))
            story.append(PageBreak())
            
            # Security metrics
            story.extend(self._create_security_metrics(report_data))
            story.append(PageBreak())
            
            # Technical risk analysis
            story.extend(self._create_technical_risk_analysis(report_data))
            story.append(PageBreak())
            
            # Recommendations
            story.extend(self._create_recommendations(report_data))
            
            # Build PDF
            doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
            
            logger.info(f"Risk Assessment PDF generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating Risk Assessment PDF: {e}")
            raise
    
    def generate_security_posture_pdf(self, report_data: Dict[str, Any]) -> str:
        """Generate professional Security Posture PDF report"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Security_Posture_Report_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            story = []
            
            # Cover page
            story.extend(self._create_cover_page("Security Posture Report", report_data))
            story.append(PageBreak())
            
            # Executive summary
            story.extend(self._create_executive_summary(report_data))
            story.append(PageBreak())
            
            # Security overview
            story.extend(self._create_security_overview(report_data))
            story.append(PageBreak())
            
            # Endpoint security
            story.extend(self._create_endpoint_security(report_data))
            story.append(PageBreak())
            
            # Vulnerability analysis
            story.extend(self._create_vulnerability_analysis(report_data))
            story.append(PageBreak())
            
            # Security tools effectiveness
            story.extend(self._create_security_tools_effectiveness(report_data))
            story.append(PageBreak())
            
            # Incident analysis
            story.extend(self._create_incident_analysis(report_data))
            story.append(PageBreak())
            
            # Data protection
            story.extend(self._create_data_protection(report_data))
            story.append(PageBreak())
            
            # Recommendations
            story.extend(self._create_recommendations(report_data))
            
            # Build PDF
            doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
            
            logger.info(f"Security Posture PDF generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating Security Posture PDF: {e}")
            raise
    
    def generate_compliance_dashboard_pdf(self, report_data: Dict[str, Any]) -> str:
        """Generate professional Compliance Dashboard PDF report"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Compliance_Dashboard_Report_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            story = []
            
            # Cover page
            story.extend(self._create_cover_page("Compliance Dashboard Report", report_data))
            story.append(PageBreak())
            
            # Executive summary
            story.extend(self._create_executive_summary(report_data))
            story.append(PageBreak())
            
            # Compliance overview
            story.extend(self._create_compliance_overview(report_data))
            story.append(PageBreak())
            
            # Control implementation
            story.extend(self._create_control_implementation(report_data))
            story.append(PageBreak())
            
            # Gap analysis
            story.extend(self._create_gap_analysis(report_data))
            story.append(PageBreak())
            
            # Audit evidence
            story.extend(self._create_audit_evidence(report_data))
            story.append(PageBreak())
            
            # Regulatory requirements
            story.extend(self._create_regulatory_requirements(report_data))
            story.append(PageBreak())
            
            # Remediation roadmap
            story.extend(self._create_remediation_roadmap(report_data))
            
            # Build PDF
            doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
            
            logger.info(f"Compliance Dashboard PDF generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating Compliance Dashboard PDF: {e}")
            raise
    
    def _create_cover_page(self, title: str, report_data: Dict[str, Any]) -> List:
        """Create professional cover page"""
        story = []
        
        # Title
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        # Subtitle
        story.append(Paragraph("Security Assessment Report", self.styles['CustomHeading1']))
        story.append(Spacer(1, 1*inch))
        
        # Report details
        generated_at = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(f"Generated: {generated_at}", self.styles['CustomBody']))
        story.append(Paragraph("Confidential - Internal Use Only", self.styles['CustomBody']))
        story.append(Spacer(1, 1*inch))
        
        # Executive summary box
        story.append(Paragraph("Executive Summary", self.styles['CustomHeading2']))
        
        # Get executive summary from report data
        executive_summary = self._extract_executive_summary(report_data)
        story.append(Paragraph(executive_summary, self.styles['ExecutiveSummary']))
        
        return story
    
    def _create_executive_summary(self, report_data: Dict[str, Any]) -> List:
        """Create executive summary section"""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        # Extract key metrics
        key_metrics = self._extract_key_metrics(report_data)
        
        # Create metrics table
        if key_metrics:
            table_data = [["Metric", "Value", "Status"]]
            for metric, value, status in key_metrics:
                table_data.append([metric, str(value), status])
            
            table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
        
        # Executive summary text
        executive_summary = self._extract_executive_summary(report_data)
        story.append(Paragraph(executive_summary, self.styles['ExecutiveSummary']))
        
        return story
    
    def _create_risk_overview(self, report_data: Dict[str, Any]) -> List:
        """Create risk overview section"""
        story = []
        
        story.append(Paragraph("Risk Overview", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        # Find risk data
        risk_data = self._find_section_data(report_data, 'overall_risk')
        if risk_data:
            story.append(Paragraph(f"Overall Risk Score: {risk_data.get('score', 'N/A')}", self.styles['CustomBody']))
            story.append(Paragraph(f"Risk Level: {risk_data.get('level', 'N/A').upper()}", self.styles['CustomBody']))
            story.append(Paragraph(f"Trend: {risk_data.get('trend', 'N/A')}", self.styles['CustomBody']))
            story.append(Spacer(1, 12))
        
        # Risk matrix
        risk_matrix = self._find_section_data(report_data, 'risk_matrix')
        if risk_matrix:
            story.append(Paragraph("Risk Matrix", self.styles['CustomHeading2']))
            story.extend(self._create_risk_matrix_table(risk_matrix))
        
        return story
    
    def _create_asset_inventory(self, report_data: Dict[str, Any]) -> List:
        """Create asset inventory section"""
        story = []
        
        story.append(Paragraph("Asset Inventory", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        asset_data = self._find_section_data(report_data, 'asset_inventory')
        if asset_data:
            # Summary
            story.append(Paragraph(f"Total Assets: {asset_data.get('total_assets', 0)}", self.styles['CustomBody']))
            story.append(Spacer(1, 12))
            
            # Detailed assets table
            detailed_assets = asset_data.get('detailed_assets', [])
            if detailed_assets:
                story.append(Paragraph("Asset Details", self.styles['CustomHeading2']))
                
                table_data = [["Hostname", "IP Address", "OS", "Criticality", "Security Status", "Vulnerabilities"]]
                for asset in detailed_assets:
                    table_data.append([
                        asset.get('hostname', ''),
                        asset.get('ip_address', ''),
                        asset.get('os_type', ''),
                        asset.get('criticality', ''),
                        asset.get('security_status', ''),
                        str(asset.get('vulnerability_count', 0))
                    ])
                
                table = Table(table_data, colWidths=[1.2*inch, 1.2*inch, 1*inch, 0.8*inch, 1*inch, 0.8*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8)
                ]))
                
                story.append(table)
        
        return story
    
    def _create_user_access_review(self, report_data: Dict[str, Any]) -> List:
        """Create user access review section"""
        story = []
        
        story.append(Paragraph("User Access Review", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        access_data = self._find_section_data(report_data, 'user_access_review')
        if access_data:
            # Summary
            story.append(Paragraph(f"Total Users: {access_data.get('total_users', 0)}", self.styles['CustomBody']))
            story.append(Paragraph(f"Privileged Users: {access_data.get('privileged_users', 0)}", self.styles['CustomBody']))
            story.append(Paragraph(f"Users without MFA: {access_data.get('users_without_mfa', 0)}", self.styles['CustomBody']))
            story.append(Spacer(1, 12))
            
            # Detailed users table
            detailed_users = access_data.get('detailed_users', [])
            if detailed_users:
                story.append(Paragraph("User Details", self.styles['CustomHeading2']))
                
                table_data = [["Username", "Department", "Access Level", "Privileged", "MFA", "Risk Score"]]
                for user in detailed_users:
                    table_data.append([
                        user.get('username', ''),
                        user.get('department', ''),
                        user.get('access_level', ''),
                        'Yes' if user.get('privileged_access') else 'No',
                        'Yes' if user.get('mfa_enabled') else 'No',
                        str(user.get('risk_score', 0))
                    ])
                
                table = Table(table_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 0.8*inch, 0.6*inch, 0.8*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8)
                ]))
                
                story.append(table)
        
        return story
    
    def _create_security_metrics(self, report_data: Dict[str, Any]) -> List:
        """Create security metrics section"""
        story = []
        
        story.append(Paragraph("Security Metrics", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        metrics_data = self._find_section_data(report_data, 'security_metrics')
        if metrics_data:
            operational_metrics = metrics_data.get('operational_metrics', {})
            incident_metrics = metrics_data.get('incident_metrics', {})
            
            # Operational metrics table
            if operational_metrics:
                story.append(Paragraph("Operational Metrics", self.styles['CustomHeading2']))
                
                table_data = [["Metric", "Current Value", "Target", "Status"]]
                table_data.append([
                    "Mean Time to Detection (Hours)",
                    str(operational_metrics.get('mean_time_to_detection_hours', 'N/A')),
                    "4.0",
                    "Good" if operational_metrics.get('mean_time_to_detection_hours', 0) <= 4.0 else "Needs Improvement"
                ])
                table_data.append([
                    "Mean Time to Response (Hours)",
                    str(operational_metrics.get('mean_time_to_response_hours', 'N/A')),
                    "24.0",
                    "Good" if operational_metrics.get('mean_time_to_response_hours', 0) <= 24.0 else "Needs Improvement"
                ])
                table_data.append([
                    "False Positive Rate (%)",
                    str(operational_metrics.get('false_positive_rate_percent', 'N/A')),
                    "5.0",
                    "Good" if operational_metrics.get('false_positive_rate_percent', 0) <= 5.0 else "Needs Improvement"
                ])
                table_data.append([
                    "Detection Coverage (%)",
                    str(operational_metrics.get('detection_coverage_percent', 'N/A')),
                    "95.0",
                    "Good" if operational_metrics.get('detection_coverage_percent', 0) >= 95.0 else "Needs Improvement"
                ])
                
                table = Table(table_data, colWidths=[2.5*inch, 1*inch, 0.8*inch, 1.2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 9)
                ]))
                
                story.append(table)
                story.append(Spacer(1, 20))
            
            # Incident metrics
            if incident_metrics:
                story.append(Paragraph("Incident Metrics", self.styles['CustomHeading2']))
                
                story.append(Paragraph(f"Incidents (Last 30 Days): {incident_metrics.get('incidents_last_30_days', 0)}", self.styles['CustomBody']))
                story.append(Paragraph(f"Resolved Incidents: {incident_metrics.get('resolved_incidents', 0)}", self.styles['CustomBody']))
                story.append(Paragraph(f"Resolution Rate: {incident_metrics.get('resolution_rate_percent', 0)}%", self.styles['CustomBody']))
                story.append(Paragraph(f"Average Severity Score: {incident_metrics.get('average_severity_score', 0)}", self.styles['CustomBody']))
        
        return story
    
    def _create_technical_risk_analysis(self, report_data: Dict[str, Any]) -> List:
        """Create technical risk analysis section"""
        story = []
        
        story.append(Paragraph("Technical Risk Analysis", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        tech_risk_data = self._find_section_data(report_data, 'technical_risk_analysis')
        if tech_risk_data:
            # Critical vulnerabilities
            critical_vulns = tech_risk_data.get('critical_vulnerabilities', [])
            if critical_vulns:
                story.append(Paragraph("Critical Vulnerabilities", self.styles['CustomHeading2']))
                
                table_data = [["Asset", "CVE", "Severity", "Status"]]
                for vuln in critical_vulns:
                    table_data.append([
                        vuln.get('asset', ''),
                        vuln.get('cve', ''),
                        vuln.get('severity', ''),
                        vuln.get('status', '')
                    ])
                
                table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.colors['accent']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 9)
                ]))
                
                story.append(table)
                story.append(Spacer(1, 20))
            
            # Compliance gaps
            compliance_gaps = tech_risk_data.get('compliance_gaps', [])
            if compliance_gaps:
                story.append(Paragraph("Compliance Gaps", self.styles['CustomHeading2']))
                for gap in compliance_gaps:
                    story.append(Paragraph(f"• {gap}", self.styles['CustomBody']))
                story.append(Spacer(1, 12))
            
            # Immediate actions
            immediate_actions = tech_risk_data.get('immediate_actions', [])
            if immediate_actions:
                story.append(Paragraph("Immediate Actions Required", self.styles['CustomHeading2']))
                for action in immediate_actions:
                    story.append(Paragraph(f"• {action}", self.styles['CustomBody']))
        
        return story
    
    def _create_recommendations(self, report_data: Dict[str, Any]) -> List:
        """Create recommendations section"""
        story = []
        
        story.append(Paragraph("Recommendations", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        # Find recommendations data
        recommendations_data = self._find_section_data(report_data, 'recommendations')
        if recommendations_data:
            recommendations = recommendations_data.get('recommendations', [])
            
            for i, rec in enumerate(recommendations, 1):
                story.append(Paragraph(f"{i}. {rec.get('title', 'Recommendation')}", self.styles['CustomHeading2']))
                story.append(Paragraph(rec.get('description', ''), self.styles['CustomBody']))
                
                if rec.get('actions'):
                    story.append(Paragraph("Actions:", self.styles['CustomBody']))
                    for action in rec.get('actions', []):
                        story.append(Paragraph(f"• {action}", self.styles['CustomBody']))
                
                if rec.get('timeline'):
                    story.append(Paragraph(f"Timeline: {rec.get('timeline')}", self.styles['CustomBody']))
                
                if rec.get('estimatedCost'):
                    story.append(Paragraph(f"Estimated Cost: {rec.get('estimatedCost')}", self.styles['CustomBody']))
                
                story.append(Spacer(1, 12))
        
        return story
    
    # Additional methods for other report types would be implemented here...
    def _create_security_overview(self, report_data: Dict[str, Any]) -> List:
        """Create security overview section for security posture report"""
        story = []
        
        story.append(Paragraph("Security Overview", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        exec_summary = self._find_section_data(report_data, 'executive_summary')
        if exec_summary:
            story.append(Paragraph(f"Overall Risk Score: {exec_summary.get('overallRiskScore', 'N/A')}", self.styles['CustomBody']))
            story.append(Paragraph(f"Security Grade: {exec_summary.get('securityGrade', 'N/A')}", self.styles['CustomBody']))
            story.append(Paragraph(f"Risk Level: {exec_summary.get('riskLevel', 'N/A')}", self.styles['CustomBody']))
            
            key_metrics = exec_summary.get('keyMetrics', {})
            if key_metrics:
                story.append(Spacer(1, 12))
                story.append(Paragraph("Key Metrics", self.styles['CustomHeading2']))
                story.append(Paragraph(f"Total Endpoints: {key_metrics.get('totalEndpoints', 0)}", self.styles['CustomBody']))
                story.append(Paragraph(f"Endpoints at Risk: {key_metrics.get('endpointsAtRisk', 0)}", self.styles['CustomBody']))
                story.append(Paragraph(f"Active Threats: {key_metrics.get('activeThreats', 0)}", self.styles['CustomBody']))
                story.append(Paragraph(f"Critical Vulnerabilities: {key_metrics.get('criticalVulnerabilities', 0)}", self.styles['CustomBody']))
        
        return story
    
    def _create_endpoint_security(self, report_data: Dict[str, Any]) -> List:
        """Create endpoint security section"""
        story = []
        
        story.append(Paragraph("Endpoint Security", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        endpoint_data = self._find_section_data(report_data, 'endpoint_security')
        if endpoint_data:
            story.append(Paragraph(f"Total Endpoints: {endpoint_data.get('totalEndpoints', 0)}", self.styles['CustomBody']))
            story.append(Paragraph(f"Endpoints at Risk: {endpoint_data.get('endpointsAtRisk', 0)}", self.styles['CustomBody']))
            story.append(Paragraph(f"Endpoints Compliant: {endpoint_data.get('endpointsCompliant', 0)}", self.styles['CustomBody']))
            
            security_controls = endpoint_data.get('securityControls', {})
            if security_controls:
                story.append(Spacer(1, 12))
                story.append(Paragraph("Security Controls Coverage", self.styles['CustomHeading2']))
                story.append(Paragraph(f"Antivirus Coverage: {security_controls.get('antivirusCoverage', 0)}%", self.styles['CustomBody']))
                story.append(Paragraph(f"Firewall Coverage: {security_controls.get('firewallCoverage', 0)}%", self.styles['CustomBody']))
                story.append(Paragraph(f"Encryption Coverage: {security_controls.get('encryptionCoverage', 0)}%", self.styles['CustomBody']))
                story.append(Paragraph(f"Patch Compliance: {security_controls.get('patchCompliance', 0)}%", self.styles['CustomBody']))
        
        return story
    
    def _create_vulnerability_analysis(self, report_data: Dict[str, Any]) -> List:
        """Create vulnerability analysis section"""
        story = []
        
        story.append(Paragraph("Vulnerability Analysis", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        vuln_data = self._find_section_data(report_data, 'vulnerabilities')
        if vuln_data:
            summary = vuln_data.get('summary', {})
            if summary:
                story.append(Paragraph("Vulnerability Summary", self.styles['CustomHeading2']))
                story.append(Paragraph(f"Critical: {summary.get('critical', 0)}", self.styles['CustomBody']))
                story.append(Paragraph(f"High: {summary.get('high', 0)}", self.styles['CustomBody']))
                story.append(Paragraph(f"Medium: {summary.get('medium', 0)}", self.styles['CustomBody']))
                story.append(Paragraph(f"Low: {summary.get('low', 0)}", self.styles['CustomBody']))
            
            details = vuln_data.get('details', [])
            if details:
                story.append(Spacer(1, 12))
                story.append(Paragraph("Vulnerability Details", self.styles['CustomHeading2']))
                
                table_data = [["Hostname", "Severity", "Vulnerability", "Recommendation"]]
                for vuln in details:
                    table_data.append([
                        vuln.get('hostname', ''),
                        vuln.get('severity', ''),
                        vuln.get('vulnerability', ''),
                        vuln.get('recommendation', '')
                    ])
                
                table = Table(table_data, colWidths=[1.2*inch, 0.8*inch, 2*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP')
                ]))
                
                story.append(table)
        
        return story
    
    def _create_security_tools_effectiveness(self, report_data: Dict[str, Any]) -> List:
        """Create security tools effectiveness section"""
        story = []
        
        story.append(Paragraph("Security Tools Effectiveness", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        tools_data = self._find_section_data(report_data, 'security_tools_effectiveness')
        if tools_data:
            coverage_analysis = tools_data.get('coverage_analysis', {})
            if coverage_analysis:
                story.append(Paragraph("Coverage Analysis", self.styles['CustomHeading2']))
                story.append(Paragraph(f"Endpoint Protection Coverage: {coverage_analysis.get('endpoint_protection_coverage', 0)}%", self.styles['CustomBody']))
                story.append(Paragraph(f"Network Monitoring Coverage: {coverage_analysis.get('network_monitoring_coverage', 0)}%", self.styles['CustomBody']))
                story.append(Paragraph(f"Log Collection Coverage: {coverage_analysis.get('log_collection_coverage', 0)}%", self.styles['CustomBody']))
                story.append(Paragraph(f"Vulnerability Scanning Coverage: {coverage_analysis.get('vulnerability_scanning_coverage', 0)}%", self.styles['CustomBody']))
            
            tool_performance = tools_data.get('tool_performance', {})
            if tool_performance:
                story.append(Spacer(1, 12))
                story.append(Paragraph("Tool Performance", self.styles['CustomHeading2']))
                story.append(Paragraph(f"Detection Accuracy: {tool_performance.get('detection_accuracy', 0)}%", self.styles['CustomBody']))
                
                false_positive_rates = tool_performance.get('false_positive_rates', {})
                if false_positive_rates:
                    story.append(Paragraph("False Positive Rates:", self.styles['CustomBody']))
                    for tool, rate in false_positive_rates.items():
                        story.append(Paragraph(f"• {tool}: {rate}%", self.styles['CustomBody']))
        
        return story
    
    def _create_incident_analysis(self, report_data: Dict[str, Any]) -> List:
        """Create incident analysis section"""
        story = []
        
        story.append(Paragraph("Incident Analysis", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        incident_data = self._find_section_data(report_data, 'incident_analysis')
        if incident_data:
            incident_summary = incident_data.get('incident_summary', {})
            if incident_summary:
                story.append(Paragraph("Incident Summary (Last 30 Days)", self.styles['CustomHeading2']))
                story.append(Paragraph(f"Total Incidents: {incident_summary.get('total_incidents_30d', 0)}", self.styles['CustomBody']))
                story.append(Paragraph(f"Resolved Incidents: {incident_summary.get('resolved_incidents', 0)}", self.styles['CustomBody']))
                story.append(Paragraph(f"Active Incidents: {incident_summary.get('active_incidents', 0)}", self.styles['CustomBody']))
                story.append(Paragraph(f"Average Resolution Time: {incident_summary.get('average_resolution_time_hours', 0)} hours", self.styles['CustomBody']))
        
        return story
    
    def _create_data_protection(self, report_data: Dict[str, Any]) -> List:
        """Create data protection section"""
        story = []
        
        story.append(Paragraph("Data Protection", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        data_protection_data = self._find_section_data(report_data, 'data_protection')
        if data_protection_data:
            story.append(Paragraph("Data protection analysis and recommendations will be included here.", self.styles['CustomBody']))
        
        return story
    
    def _create_compliance_overview(self, report_data: Dict[str, Any]) -> List:
        """Create compliance overview section"""
        story = []
        
        story.append(Paragraph("Compliance Overview", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        compliance_data = self._find_section_data(report_data, 'compliance_overview')
        if compliance_data:
            story.append(Paragraph(f"Overall Score: {compliance_data.get('overallScore', 0)}%", self.styles['CustomBody']))
            story.append(Paragraph(f"Grade: {compliance_data.get('grade', 'N/A')}", self.styles['CustomBody']))
            story.append(Paragraph(f"Status: {compliance_data.get('status', 'N/A')}", self.styles['CustomBody']))
            story.append(Paragraph(f"Trend: {compliance_data.get('trend', 'N/A')}", self.styles['CustomBody']))
        
        return story
    
    def _create_control_implementation(self, report_data: Dict[str, Any]) -> List:
        """Create control implementation section"""
        story = []
        
        story.append(Paragraph("Control Implementation", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        control_data = self._find_section_data(report_data, 'control_implementation')
        if control_data:
            story.append(Paragraph(f"Total Controls: {control_data.get('totalControls', 0)}", self.styles['CustomBody']))
            story.append(Paragraph(f"Implemented Controls: {control_data.get('implementedControls', 0)}", self.styles['CustomBody']))
            story.append(Paragraph(f"Implementation Rate: {control_data.get('implementationRate', 0)}%", self.styles['CustomBody']))
        
        return story
    
    def _create_gap_analysis(self, report_data: Dict[str, Any]) -> List:
        """Create gap analysis section"""
        story = []
        
        story.append(Paragraph("Gap Analysis", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        gap_data = self._find_section_data(report_data, 'gap_analysis')
        if gap_data:
            critical_gaps = gap_data.get('criticalGaps', [])
            if critical_gaps:
                story.append(Paragraph("Critical Gaps", self.styles['CustomHeading2']))
                for gap in critical_gaps:
                    story.append(Paragraph(f"• {gap}", self.styles['CustomBody']))
            
            high_gaps = gap_data.get('highGaps', [])
            if high_gaps:
                story.append(Spacer(1, 12))
                story.append(Paragraph("High Priority Gaps", self.styles['CustomHeading2']))
                for gap in high_gaps:
                    story.append(Paragraph(f"• {gap}", self.styles['CustomBody']))
        
        return story
    
    def _create_audit_evidence(self, report_data: Dict[str, Any]) -> List:
        """Create audit evidence section"""
        story = []
        
        story.append(Paragraph("Audit Evidence", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        audit_data = self._find_section_data(report_data, 'audit_evidence')
        if audit_data:
            story.append(Paragraph(f"Evidence Quality Score: {audit_data.get('evidence_quality_score', 0)}%", self.styles['CustomBody']))
        
        return story
    
    def _create_regulatory_requirements(self, report_data: Dict[str, Any]) -> List:
        """Create regulatory requirements section"""
        story = []
        
        story.append(Paragraph("Regulatory Requirements", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        regulatory_data = self._find_section_data(report_data, 'regulatory_requirements')
        if regulatory_data:
            story.append(Paragraph("Regulatory compliance analysis and requirements will be included here.", self.styles['CustomBody']))
        
        return story
    
    def _create_remediation_roadmap(self, report_data: Dict[str, Any]) -> List:
        """Create remediation roadmap section"""
        story = []
        
        story.append(Paragraph("Remediation Roadmap", self.styles['CustomHeading1']))
        story.append(Spacer(1, 12))
        
        roadmap_data = self._find_section_data(report_data, 'remediation_roadmap')
        if roadmap_data:
            immediate_actions = roadmap_data.get('immediate_actions', [])
            if immediate_actions:
                story.append(Paragraph("Immediate Actions", self.styles['CustomHeading2']))
                for action in immediate_actions:
                    story.append(Paragraph(f"• {action}", self.styles['CustomBody']))
            
            short_term_goals = roadmap_data.get('short_term_goals', [])
            if short_term_goals:
                story.append(Spacer(1, 12))
                story.append(Paragraph("Short-term Goals", self.styles['CustomHeading2']))
                for goal in short_term_goals:
                    story.append(Paragraph(f"• {goal}", self.styles['CustomBody']))
        
        return story
    
    def _create_risk_matrix_table(self, risk_matrix_data: Dict[str, Any]) -> List:
        """Create risk matrix table"""
        story = []
        
        matrix = risk_matrix_data.get('matrix', {})
        if matrix:
            table_data = [["Risk Level", "Count"]]
            for level, risks in matrix.items():
                table_data.append([level.title(), str(len(risks))])
            
            table = Table(table_data, colWidths=[2*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        
        return story
    
    def _add_header_footer(self, canvas, doc):
        """Add professional header and footer to pages"""
        canvas.saveState()
        
        # Header
        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(self.colors['primary'])
        canvas.drawString(72, A4[1] - 50, "Security Assessment Report")
        
        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(self.colors['text'])
        canvas.drawString(72, 30, f"Generated: {datetime.now().strftime('%B %d, %Y')}")
        canvas.drawRightString(A4[0] - 72, 30, f"Page {doc.page}")
        
        canvas.restoreState()
    
    def _find_section_data(self, report_data: Dict[str, Any], section_type: str) -> Optional[Dict[str, Any]]:
        """Find specific section data in report"""
        data = report_data.get('data', [])
        for item in data:
            if item.get('type') == section_type:
                return item
        return None
    
    def _extract_executive_summary(self, report_data: Dict[str, Any]) -> str:
        """Extract executive summary from report data"""
        # Try to find executive summary in different sections
        exec_summary = self._find_section_data(report_data, 'executive_summary')
        if exec_summary:
            return f"This security assessment reveals a {exec_summary.get('riskLevel', 'unknown')} risk level with an overall score of {exec_summary.get('overallRiskScore', 'N/A')}. The security grade is {exec_summary.get('securityGrade', 'N/A')}."
        
        overall_risk = self._find_section_data(report_data, 'overall_risk')
        if overall_risk:
            return f"This security assessment reveals a {overall_risk.get('level', 'unknown')} risk level with a score of {overall_risk.get('score', 'N/A')}. The risk trend is {overall_risk.get('trend', 'unknown')}."
        
        return "This comprehensive security assessment provides detailed analysis of the organization's security posture, including risk assessment, compliance status, and actionable recommendations for improvement."
    
    def _extract_key_metrics(self, report_data: Dict[str, Any]) -> List[tuple]:
        """Extract key metrics for executive summary table"""
        metrics = []
        
        # Risk assessment metrics
        overall_risk = self._find_section_data(report_data, 'overall_risk')
        if overall_risk:
            metrics.append(("Risk Score", overall_risk.get('score', 'N/A'), overall_risk.get('level', 'N/A')))
        
        # Security posture metrics
        exec_summary = self._find_section_data(report_data, 'executive_summary')
        if exec_summary:
            metrics.append(("Security Grade", exec_summary.get('securityGrade', 'N/A'), exec_summary.get('riskLevel', 'N/A')))
        
        # Compliance metrics
        compliance_overview = self._find_section_data(report_data, 'compliance_overview')
        if compliance_overview:
            metrics.append(("Compliance Score", f"{compliance_overview.get('overallScore', 0)}%", compliance_overview.get('grade', 'N/A')))
        
        return metrics

# 📋 COMPLETE API STRUCTURE - ALL 3 ENDPOINTS

## 🎯 **API ENDPOINTS OVERVIEW**

All 3 APIs follow the same consistent structure with `status`, `data`, and `metadata` fields.

---

## 1️⃣ **RISK ASSESSMENT API**

### **POST** `/api/backend/risk-assessment`
**Purpose:** Generate a new risk assessment report

#### **Request:**
```json
POST /api/backend/risk-assessment
Content-Type: application/json

{
  "time_range_hours": 24,
  "include_ml_analysis": true
}
```

#### **Response Structure:**
```json
{
  "status": "success",
  "data": [
    {
      "type": "download_info",
      "message": "Risk assessment report generated successfully",
      "download_url": "/api/downloads/Risk_Assessment_Report_20251012_100726.pdf",
      "filename": "Risk_Assessment_Report_20251012_100726.pdf",
      "file_size": "2.3 MB",
      "generated_at": "2025-10-12T10:07:26.452877",
      "report_type": "risk_assessment",
      "enhanced": true,
      "cached": false,
      "freshly_generated": true
    }
  ],
  "metadata": {
    "reportId": "risk_assessment_20251012_100726",
    "generatedAt": "2025-10-12T10:07:26.452877"
  }
}
```

### **GET** `/api/backend/risk-assessment`
**Purpose:** Retrieve cached risk assessment report

#### **Response Structure:**
```json
{
  "status": "success",
  "data": [
    {
      "type": "cached_report",
      "message": "Risk assessment report retrieved from cache",
      "download_url": "/api/downloads/Risk_Assessment_Report_20251012_100726.pdf",
      "filename": "Risk_Assessment_Report_20251012_100726.pdf",
      "file_size": "2.3 MB",
      "generated_at": "2025-10-12T10:07:26.452877",
      "report_type": "risk_assessment",
      "enhanced": true,
      "cached": true,
      "freshly_generated": false
    }
  ],
  "metadata": {
    "reportId": "risk_assessment_20251012_100726",
    "generatedAt": "2025-10-12T10:07:26.452877"
  }
}
```

---

## 2️⃣ **SECURITY POSTURE REPORT API**

### **POST** `/api/backend/security-posture-report`
**Purpose:** Generate a new security posture report

#### **Request:**
```json
POST /api/backend/security-posture-report
Content-Type: application/json

{
  "time_range_hours": 24,
  "include_ml_analysis": true
}
```

#### **Response Structure:**
```json
{
  "status": "success",
  "data": [
    {
      "type": "download_info",
      "message": "Security posture report generated successfully",
      "download_url": "/api/downloads/Security_Posture_Report_20251012_100726.pdf",
      "filename": "Security_Posture_Report_20251012_100726.pdf",
      "file_size": "2.8 MB",
      "generated_at": "2025-10-12T10:07:26.452877",
      "report_type": "security_posture",
      "enhanced": true,
      "cached": false,
      "freshly_generated": true
    }
  ],
  "metadata": {
    "reportId": "security_posture_20251012_100726",
    "generatedAt": "2025-10-12T10:07:26.452877"
  }
}
```

### **GET** `/api/backend/security-posture-report`
**Purpose:** Retrieve cached security posture report

#### **Response Structure:**
```json
{
  "status": "success",
  "data": [
    {
      "type": "cached_report",
      "message": "Security posture report retrieved from cache",
      "download_url": "/api/downloads/Security_Posture_Report_20251012_100726.pdf",
      "filename": "Security_Posture_Report_20251012_100726.pdf",
      "file_size": "2.8 MB",
      "generated_at": "2025-10-12T10:07:26.452877",
      "report_type": "security_posture",
      "enhanced": true,
      "cached": true,
      "freshly_generated": false
    }
  ],
  "metadata": {
    "reportId": "security_posture_20251012_100726",
    "generatedAt": "2025-10-12T10:07:26.452877"
  }
}
```

---

## 3️⃣ **COMPLIANCE DASHBOARD API**

### **POST** `/api/backend/compliance-dashboard`
**Purpose:** Generate a new compliance dashboard report

#### **Request:**
```json
POST /api/backend/compliance-dashboard
Content-Type: application/json

{
  "time_range_hours": 24,
  "include_ml_analysis": true
}
```

#### **Response Structure:**
```json
{
  "status": "success",
  "data": [
    {
      "type": "download_info",
      "message": "Compliance dashboard report generated successfully",
      "download_url": "/api/downloads/Compliance_Dashboard_Report_20251012_100726.pdf",
      "filename": "Compliance_Dashboard_Report_20251012_100726.pdf",
      "file_size": "3.1 MB",
      "generated_at": "2025-10-12T10:07:26.452877",
      "report_type": "compliance_dashboard",
      "enhanced": true,
      "cached": false,
      "freshly_generated": true
    }
  ],
  "metadata": {
    "reportId": "compliance_dashboard_20251012_100726",
    "generatedAt": "2025-10-12T10:07:26.452877"
  }
}
```

### **GET** `/api/backend/compliance-dashboard`
**Purpose:** Retrieve cached compliance dashboard report

#### **Response Structure:**
```json
{
  "status": "success",
  "data": [
    {
      "type": "cached_report",
      "message": "Compliance dashboard report retrieved from cache",
      "download_url": "/api/downloads/Compliance_Dashboard_Report_20251012_100726.pdf",
      "filename": "Compliance_Dashboard_Report_20251012_100726.pdf",
      "file_size": "3.1 MB",
      "generated_at": "2025-10-12T10:07:26.452877",
      "report_type": "compliance_dashboard",
      "enhanced": true,
      "cached": true,
      "freshly_generated": false
    }
  ],
  "metadata": {
    "reportId": "compliance_dashboard_20251012_100726",
    "generatedAt": "2025-10-12T10:07:26.452877"
  }
}
```

---

## 📊 **FIELD DESCRIPTIONS**

### **Main Response Fields:**
- **`status`**: Always "success" for successful operations
- **`data`**: Array containing report information and download details
- **`metadata`**: Contains report ID and generation timestamp

### **Data Array Fields:**
- **`type`**: Either "download_info" (POST) or "cached_report" (GET)
- **`message`**: Human-readable status message
- **`download_url`**: URL to download the PDF report
- **`filename`**: Name of the generated PDF file
- **`file_size`**: Size of the PDF file in MB
- **`generated_at`**: ISO timestamp when report was generated
- **`report_type`**: Type of report (risk_assessment, security_posture, compliance_dashboard)
- **`enhanced`**: Always true (reports include enhanced technical details)
- **`cached`**: true for GET requests, false for POST requests
- **`freshly_generated`**: true for POST requests, false for GET requests

### **Metadata Fields:**
- **`reportId`**: Unique identifier for the report
- **`generatedAt`**: ISO timestamp when report was generated

---

## 🔄 **API BEHAVIOR**

### **POST Endpoints:**
1. Generate fresh report with enhanced technical details
2. Create professional PDF with ReportLab
3. Save report to cache for future retrieval
4. Return download information in `data` array
5. Set `cached: false` and `freshly_generated: true`

### **GET Endpoints:**
1. Retrieve cached report from database
2. Return download information in `data` array
3. Set `cached: true` and `freshly_generated: false`
4. If no cached report exists, return appropriate error

---

## 🎯 **USAGE PATTERNS**

### **Frontend Button Click (POST):**
```javascript
// User clicks "Generate Risk Assessment" button
fetch('/api/backend/risk-assessment', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ time_range_hours: 24 })
})
.then(response => response.json())
.then(data => {
  // Show download link: data.data[0].download_url
  // Show filename: data.data[0].filename
  // Show file size: data.data[0].file_size
});
```

### **Retrieve Cached Report (GET):**
```javascript
// User wants to download previously generated report
fetch('/api/backend/risk-assessment')
.then(response => response.json())
.then(data => {
  // Show download link: data.data[0].download_url
  // Show generation time: data.data[0].generated_at
});
```

---

## ✅ **CONSISTENT STRUCTURE**

All 3 APIs follow the exact same structure:
- ✅ Same response format
- ✅ Same field names
- ✅ Same data types
- ✅ Same metadata structure
- ✅ Same error handling
- ✅ Same caching behavior
- ✅ Same PDF generation
- ✅ Same download URLs

**This ensures consistent frontend integration and user experience across all report types!** 🚀

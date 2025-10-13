# 🚨 HARDCODED VALUES ANALYSIS - APT SCENARIOS

## ❌ **HARDCODED VALUES FOUND**

### **1. Network Addresses (CRITICAL)**
```python
# Hardcoded IP ranges and addresses
'192.168.1.0/24'     # Network scan targets
'192.168.1.100'      # SSH brute force target
'192.168.1.200'      # Data exfiltration target
'192.168.100.0/24'   # Scenario network
'192.168.101.0/24'   # Target network  
'192.168.102.0/24'   # Attack network
'10.0.1.100'         # Example hosts
'10.0.1.101'         # Example hosts
```

### **2. Credentials (CRITICAL)**
```python
# Hardcoded usernames and passwords
'admin'              # Default username for brute force
'password123'        # Default password
'hacker'             # Default attack user
'passwords.txt'      # Password file reference
```

### **3. Service Endpoints (MEDIUM)**
```python
# Hardcoded service endpoints
'http://localhost:11434'  # Ollama endpoint
'http://attacker.com/data.php'  # Exfiltration endpoint
```

### **4. Container Images (MEDIUM)**
```python
# Hardcoded container image names
'soc/windows-domain-controller:latest'
'soc/apt-simulator:latest'
'soc/file-server:latest'
'soc/ransomware-sim:latest'
'soc/database-server:latest'
'soc/data-exfil-sim:latest'
'soc/web-server:latest'
'soc/web-attacker:latest'
```

### **5. Network Names (LOW)**
```python
# Hardcoded network names
'soc-target-network'
'soc-attack-network'
'soc-bridge-network'
'soc-scenario-{scenario_id}'
```

---

## 🎯 **IMPACT ASSESSMENT**

### **CRITICAL Issues:**
- **Network Addresses:** Will fail in different network environments
- **Credentials:** Security risk and unrealistic for real scenarios
- **Target IPs:** Scenarios won't work on actual networks

### **MEDIUM Issues:**
- **Service Endpoints:** May not work in different deployments
- **Container Images:** May not exist in target environments

### **LOW Issues:**
- **Network Names:** Cosmetic but should be configurable

---

## ✅ **RECOMMENDED FIXES**

### **1. Make Network Addresses Dynamic**
```python
# Instead of hardcoded:
'script': 'nmap -sS -O -A 192.168.1.0/24'

# Use dynamic discovery:
'script': f'nmap -sS -O -A {network_context["target_network"]}'
```

### **2. Use Environment-Based Credentials**
```python
# Instead of hardcoded:
'hydra -l admin -P passwords.txt ssh://192.168.1.100'

# Use discovered credentials:
'hydra -l {discovered_user} -P {wordlist} ssh://{target_ip}'
```

### **3. Dynamic Target Discovery**
```python
# Instead of hardcoded IPs:
'target_ip': '192.168.1.100'

# Use network discovery:
'target_ip': network_context['discovered_targets'][0]['ip']
```

### **4. Configurable Service Endpoints**
```python
# Instead of hardcoded:
'endpoint': 'http://localhost:11434'

# Use configuration:
'endpoint': config.get('ollama_endpoint', 'http://localhost:11434')
```

---

## 🔧 **FILES THAT NEED UPDATES**

### **High Priority:**
1. `server/agents/attack_agent/langchain_attack_agent.py`
   - Lines 773, 781, 791, 799: Hardcoded network addresses
   - Lines 819, 837, 925, 933: Hardcoded credentials

2. `server/agents/attack_agent/gpt_scenario_requester.py`
   - Lines 483, 496: Hardcoded example hosts

### **Medium Priority:**
3. `server/agents/attack_agent/ai_attacker_brain.py`
   - Line 78: Hardcoded Ollama endpoint

4. `server/agents/attack_agent/adaptive_attack_orchestrator.py`
   - Line 203: Hardcoded Ollama endpoint

5. `server/agents/attack_agent/creative_attack_planner.py`
   - Lines 70, 77, 646: Hardcoded Ollama endpoints

### **Low Priority:**
6. Container image references
7. Network name references

---

## 🚀 **IMPLEMENTATION STRATEGY**

### **Phase 1: Critical Fixes (Network & Credentials)**
1. Replace hardcoded IP addresses with dynamic discovery
2. Replace hardcoded credentials with environment variables
3. Implement network context-based targeting

### **Phase 2: Service Configuration**
1. Make service endpoints configurable
2. Add environment variable support
3. Implement fallback mechanisms

### **Phase 3: Container & Network Names**
1. Make container images configurable
2. Generate dynamic network names
3. Add customization options

---

## 📊 **BENEFITS OF FIXING**

### **Real-World Compatibility:**
- **Dynamic Targeting:** Works on any network environment
- **Realistic Scenarios:** Uses actual discovered targets
- **Flexible Deployment:** Adapts to different network topologies

### **Security Improvements:**
- **No Hardcoded Credentials:** Uses discovered or configured credentials
- **Environment-Specific:** Adapts to actual network conditions
- **Realistic Testing:** More authentic attack scenarios

### **Operational Benefits:**
- **Easier Deployment:** Works out-of-the-box on any network
- **Better Testing:** More realistic attack simulations
- **Reduced Maintenance:** Less manual configuration required

---

## ⚠️ **CURRENT LIMITATIONS**

### **Network Compatibility:**
- **Fixed IP Ranges:** Only works on 192.168.1.x networks
- **Hardcoded Targets:** Won't work on different network topologies
- **Static Credentials:** Unrealistic for real-world testing

### **Deployment Issues:**
- **Environment Dependencies:** Requires specific network setup
- **Manual Configuration:** Needs network-specific adjustments
- **Limited Portability:** Hard to deploy in different environments

---

## 🎯 **NEXT STEPS**

### **Immediate Actions:**
1. **Identify all hardcoded values** in the codebase
2. **Create configuration system** for dynamic values
3. **Implement network discovery** for target identification
4. **Add environment variable support** for credentials

### **Implementation Plan:**
1. **Phase 1:** Fix critical network and credential hardcoding
2. **Phase 2:** Make service endpoints configurable
3. **Phase 3:** Add full customization support

**The APT scenarios system needs to be made dynamic and configurable to work in real-world environments!** 🚀

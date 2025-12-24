# Security Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Generate Credentials
```bash
# Generate secure secret key (32+ characters)
export NETREAPER_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')

# Generate secure password (24+ characters)
export NETREAPER_PASSWORD=$(python -c 'import secrets; print(secrets.token_urlsafe(24))')

# Save to .env file (don't commit this!)
echo "NETREAPER_SECRET=$NETREAPER_SECRET" > .env
echo "NETREAPER_PASSWORD=$NETREAPER_PASSWORD" >> .env
```

### Step 2: Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install pkexec for secure sudo (Linux only)
sudo apt-get install policykit-1  # Debian/Ubuntu
# or
sudo yum install polkit           # RHEL/CentOS
```

### Step 3: Run Security Tests
```bash
# Quick security validation
python tests/run_security_tests.py

# Full test suite (if pytest installed)
pytest tests/test_security.py -v
```

### Step 4: Start Application

**GUI (Linux/Mac):**
```bash
python3 netreaper_gui.py
```

**GUI (Windows):**
```bash
python netreaper_gui_windows.py
```

**API Server (Development):**
```bash
# Load environment variables
source .env  # or: set -a; source .env; set +a

# Start server
python main.py
```

**API Server (Production with HTTPS):**
```bash
# Generate SSL certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365

# Configure SSL
export NETREAPER_SSL_KEY=key.pem
export NETREAPER_SSL_CERT=cert.pem

# Start server
python main.py
```

## 🔒 Security Features Enabled

### ✅ Command Injection Prevention
- All commands use `shell=False`
- Shell metacharacters blocked
- Command parsing with `shlex.split()`

### ✅ Credential Protection
- Passwords redacted from logs
- API keys sanitized in output
- Tokens hidden in history
- Secure sudo with pkexec

### ✅ Authentication & Authorization
- JWT token authentication
- Rate limiting (5 attempts/5 min)
- Constant-time password comparison
- Token expiration (1 hour)

### ✅ Input Validation
- Command structure validation
- Path traversal protection
- Tool availability checks
- Pydantic request models

### ✅ Output Sanitization
- Sensitive patterns redacted
- Logs are safe to share
- History files sanitized

## 🛡️ Security Checklist

### Before First Use
- [ ] Generated strong credentials
- [ ] Saved credentials to .env file
- [ ] Added .env to .gitignore
- [ ] Ran security tests
- [ ] Installed pkexec (Linux)

### Before Production Deployment
- [ ] Configured HTTPS with valid certificates
- [ ] Set CORS allowed origins
- [ ] Configured firewall rules
- [ ] Set up log monitoring
- [ ] Tested authentication
- [ ] Verified rate limiting

### Regular Maintenance
- [ ] Rotate credentials monthly
- [ ] Update dependencies weekly
- [ ] Review logs weekly
- [ ] Run security tests on changes

## 🔧 Common Commands

### Generate Credentials
```bash
# Secret key (32+ chars)
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Password (24+ chars)
python -c 'import secrets; print(secrets.token_urlsafe(24))'

# Pairing code (8 chars)
python -c 'import secrets; print(secrets.token_urlsafe(8).upper())'
```

### Test Security
```bash
# Run security tests
python tests/run_security_tests.py

# Check for shell=True (should be empty)
grep -r "shell=True" *.py

# Verify sanitization
grep -r "_sanitize" *.py
```

### Generate SSL Certificates
```bash
# Self-signed (testing)
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365

# Let's Encrypt (production)
certbot certonly --standalone -d yourdomain.com
```

### Monitor Security
```bash
# Watch logs
tail -f /var/log/netreaper/*.log

# Count failed auth attempts
grep "Authentication failed" /var/log/netreaper/*.log | wc -l

# Check rate limiting
grep "rate limit" /var/log/netreaper/*.log
```

## 🚨 Emergency Procedures

### If Credentials Compromised
```bash
# 1. Generate new credentials immediately
export NETREAPER_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
export NETREAPER_PASSWORD=$(python -c 'import secrets; print(secrets.token_urlsafe(24))')

# 2. Restart server
pkill -f "python main.py"
python main.py

# 3. Review logs for unauthorized access
grep "Authentication" /var/log/netreaper/*.log
```

### If Vulnerability Discovered
```bash
# 1. Update to latest version
git pull origin main
pip install --upgrade -r requirements.txt

# 2. Run security tests
python tests/run_security_tests.py

# 3. Restart services
# (restart commands for your deployment)
```

## 📚 Quick Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NETREAPER_SECRET` | Yes | None | JWT signing key (32+ chars) |
| `NETREAPER_PASSWORD` | Yes | None | Authentication password |
| `NETREAPER_PORT` | No | 8000 | Server port |
| `NETREAPER_ALLOWED_ORIGINS` | No | localhost | CORS origins |
| `NETREAPER_SSL_KEY` | No | None | SSL private key path |
| `NETREAPER_SSL_CERT` | No | None | SSL certificate path |

### Security Patterns Redacted

| Pattern | Example | Redacted As |
|---------|---------|-------------|
| Password | `password=secret` | `password=***REDACTED***` |
| API Key | `api_key=sk_123` | `api_key=***REDACTED***` |
| Token | `token: ghp_abc` | `token: ***REDACTED***` |
| Secret | `secret=value` | `secret=***REDACTED***` |
| Auth Header | `Authorization: Bearer xyz` | `Authorization: ***REDACTED***` |

### Rate Limiting

- **Max Attempts:** 5
- **Time Window:** 5 minutes
- **Scope:** Per client
- **Action:** Block further attempts

### Token Expiration

- **Default:** 1 hour
- **Claims:** exp, iat, jti
- **Algorithm:** HS256
- **Refresh:** Re-authenticate

## 🆘 Getting Help

### Documentation
- [Full Security Guide](SECURITY.md)
- [Implementation Details](SECURITY_IMPLEMENTATION_SUMMARY.md)
- [Deployment Checklist](SECURITY_CHECKLIST.md)
- [Design Decisions](DECISIONS.md)

### Support
- **Security Issues:** [Open Security Advisory](https://github.com/Nerds489/NETREAPER/security/advisories/new)
- **General Help:** [Create GitHub Issue](https://github.com/Nerds489/NETREAPER/issues)

### Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

**Last Updated:** 2025-12-21  
**Version:** 1.0

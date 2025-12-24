# Security Checklist

## Pre-Deployment Security Checklist

Use this checklist before deploying NetReaper in any environment.

### Environment Configuration

- [ ] `NETREAPER_SECRET` is set and at least 32 characters long
- [ ] `NETREAPER_PASSWORD` is set and uses a strong password
- [ ] `NETREAPER_ALLOWED_ORIGINS` is configured (not using defaults)
- [ ] SSL certificates are configured for HTTPS
- [ ] Environment variables are not committed to version control
- [ ] `.env` file is in `.gitignore`

### Server Security

- [ ] Server is running with HTTPS enabled
- [ ] Server is running as non-root user
- [ ] Firewall rules restrict access to authorized IPs only
- [ ] Rate limiting is enabled and configured
- [ ] Logs are being collected and monitored
- [ ] Log rotation is configured
- [ ] Backup strategy is in place

### Application Security

- [ ] All dependencies are up to date
- [ ] Security tests pass (`pytest tests/test_security.py`)
- [ ] No hardcoded credentials in code
- [ ] Input validation is enabled
- [ ] Output sanitization is enabled
- [ ] Command whitelist is properly configured
- [ ] Path traversal protection is active

### Network Security

- [ ] Reverse proxy is configured (nginx/Caddy)
- [ ] CORS is properly configured
- [ ] VPN or private network is used for remote access
- [ ] DDoS protection is in place
- [ ] Network segmentation is implemented

### Monitoring and Auditing

- [ ] Failed authentication attempts are logged
- [ ] Rate limit violations are alerted
- [ ] Unusual command patterns are monitored
- [ ] Log analysis tools are configured
- [ ] Incident response plan is documented

### Compliance and Documentation

- [ ] Authorization documentation is in place
- [ ] Scope of testing is clearly defined
- [ ] Responsible disclosure policy is understood
- [ ] Security policy is reviewed and accepted
- [ ] Team members are trained on secure usage

## Post-Deployment Security Checklist

### Regular Maintenance

- [ ] Credentials are rotated monthly
- [ ] Dependencies are updated weekly
- [ ] Security patches are applied within 7 days
- [ ] Logs are reviewed weekly
- [ ] Access logs are audited monthly
- [ ] Unused accounts are disabled

### Incident Response

- [ ] Incident response plan is tested quarterly
- [ ] Security contacts are up to date
- [ ] Backup restoration is tested monthly
- [ ] Disaster recovery plan is documented
- [ ] Communication plan is in place

### Continuous Improvement

- [ ] Security tests are run on every deployment
- [ ] Vulnerability scans are performed monthly
- [ ] Penetration testing is conducted annually
- [ ] Security training is provided quarterly
- [ ] Security metrics are tracked and reviewed

## Security Testing Commands

### Run All Security Tests
```bash
pytest tests/test_security.py -v
```

### Check for Vulnerabilities
```bash
# Check Python dependencies
pip-audit

# Static analysis
bandit -r . -ll

# Type checking
mypy netreaper_gui.py netreaper_gui_windows.py main.py
```

### Verify Configuration
```bash
# Check environment variables
python -c "import os; print('SECRET:', 'SET' if os.getenv('NETREAPER_SECRET') else 'MISSING'); print('PASSWORD:', 'SET' if os.getenv('NETREAPER_PASSWORD') else 'MISSING')"

# Verify SSL certificates
openssl x509 -in cert.pem -text -noout

# Test HTTPS connection
curl -v https://localhost:8443/
```

### Monitor Security
```bash
# Watch authentication logs
tail -f /var/log/netreaper/auth.log

# Monitor failed attempts
grep "Authentication failed" /var/log/netreaper/*.log | wc -l

# Check rate limiting
grep "rate limit" /var/log/netreaper/*.log
```

## Common Security Issues and Solutions

### Issue: Command Injection
**Symptom:** Unexpected commands are executed
**Solution:** Ensure `shell=False` is used in all subprocess calls
**Verification:** Run `grep -r "shell=True" *.py` (should return no results)

### Issue: Credential Leakage
**Symptom:** Passwords appear in logs or UI
**Solution:** Verify output sanitization is enabled
**Verification:** Check logs for `***REDACTED***` patterns

### Issue: Unauthorized Access
**Symptom:** API endpoints accessible without authentication
**Solution:** Ensure all endpoints use `Depends(get_current_user)`
**Verification:** Test endpoints without JWT token (should return 401)

### Issue: Weak Credentials
**Symptom:** Easy to guess passwords or short secret keys
**Solution:** Use `secrets.token_urlsafe()` to generate strong credentials
**Verification:** Check credential length (min 32 chars for SECRET, 24 for PASSWORD)

### Issue: Missing HTTPS
**Symptom:** Server running on HTTP
**Solution:** Configure SSL certificates and set environment variables
**Verification:** Check server startup logs for HTTPS confirmation

## Emergency Response

### If Credentials Are Compromised

1. **Immediate Actions:**
   ```bash
   # Generate new credentials
   export NETREAPER_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
   export NETREAPER_PASSWORD=$(python -c 'import secrets; print(secrets.token_urlsafe(24))')
   
   # Restart server
   pkill -f "python main.py"
   python main.py
   ```

2. **Invalidate old tokens** - All existing JWT tokens will be invalid with new SECRET

3. **Review logs** - Check for unauthorized access
   ```bash
   grep "Authentication failed" /var/log/netreaper/*.log
   ```

4. **Notify stakeholders** - Inform team of credential rotation

### If Vulnerability Is Discovered

1. **Assess impact** - Determine severity and affected systems
2. **Apply patch** - Update to latest version or apply hotfix
3. **Verify fix** - Run security tests
4. **Document incident** - Record details for future reference
5. **Review procedures** - Update security checklist if needed

## Security Contacts

- **Security Team:** [security@example.com]
- **Incident Response:** [incident@example.com]
- **On-Call:** [oncall@example.com]

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

Last Updated: 2025-12-21

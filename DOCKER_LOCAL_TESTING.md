# Local Docker Testing Guide

Before deploying to AWS EC2, test your Docker setup locally to catch any issues early.

## Prerequisites
- Docker Desktop installed ([download here](https://www.docker.com/products/docker-desktop))
- Your project code ready
- `.env.example` configured (if needed)

## Testing Steps

### 1. Build Docker Image Locally
```bash
cd PiMediaServer
docker-compose build
```

**Expected output:**
```
Building streamlit...
Successfully tagged pi-media-server:latest
```

### 2. Run Locally
```bash
docker-compose up
```

**Expected output:**
```
streamlit  |   You can now view your Streamlit app in your browser.
streamlit  |   URL: http://localhost:8501
```

### 3. Access Application
- Open browser: `http://localhost:8501`
- You should see the login page

### 4. Verify Functionality

#### Test 1: Authentication
1. Register a new user
2. Try logging in
3. Verify data persists in `data/users.json`

#### Test 2: Media Library
1. Upload a small test file
2. Check if file appears in Media Library
3. Verify file stored in `media/uploads/`

#### Test 3: Network Storage
1. Go to Settings → Network Storage
2. Configure your Raspberry Pi details
3. Try connection test (will fail if Pi not on same network)

### 5. Check Container Logs
```bash
docker-compose logs -f
```

### 6. Monitor Resources
```bash
docker stats
```

**Note for t2.micro:** Watch memory usage (should stay <500MB)

### 7. Stop Container
```bash
docker-compose down
```

## Troubleshooting Local Testing

### Issue: "Port 8501 already in use"
```bash
# Kill existing process
docker-compose down -v

# Or use different port
docker run -p 9000:8501 ...
```

### Issue: "No space left on device"
```bash
# Clean up Docker
docker system prune -a
docker volume prune
```

### Issue: "Module not found" error
```bash
# Rebuild without cache
docker-compose build --no-cache
```

### Issue: "Permission denied" on volumes
```bash
# Fix permissions
chmod 777 data config media logs temp

# Rebuild
docker-compose up --build
```

## Local vs AWS Differences

| Aspect | Local | AWS EC2 |
|--------|-------|---------|
| Data Persistence | Via Docker volumes | Via mounted directories |
| SMB Mounting | Works if Pi on same LAN | Requires VPN/specific setup |
| Restart Behavior | Manual | Auto (t2 restarts) |
| Resource Limits | Depends on host | Limited to t2.micro |
| Network | Local/private | Public internet |

## Performance Baseline

Record these metrics locally to compare with AWS:

```bash
# Check startup time
time docker-compose up
# Should take: 10-20 seconds

# Check memory usage
docker stats --no-stream
# Streamlit should use: 300-400 MB

# Check disk space
du -sh media logs
# Typical usage: 50 MB initially
```

## Pre-Deployment Checklist

- [ ] Docker build completes without errors
- [ ] App accessible at http://localhost:8501
- [ ] Can register new user
- [ ] Can upload test files
- [ ] Files persist after container restart
- [ ] Logs show no error messages
- [ ] Memory usage < 500 MB
- [ ] No permission errors on volumes

## Common Issues & Fixes

### Poetry/pip issues
```bash
# Clear cache
docker-compose build --no-cache

# Or rebuild from fresh
docker system prune -a
docker-compose build
```

### Streamlit session issues
```bash
# Clear Streamlit cache
rm -rf .streamlit/cache

# Restart
docker-compose restart
```

### Network issues
```bash
# Test connectivity inside container
docker exec pi-media-server ping 192.168.1.100

# Check container network
docker network inspect pi-media-server_default
```

## Performance Optimization Tips

Before deploying to AWS:

1. **Disable unnecessary features for testing:**
   ```python
   # In app.py, set:
   GENERATE_THUMBNAILS = False
   ENABLE_CACHING = True
   ```

2. **Test with actual network storage:**
   ```bash
   # Add to docker-compose.yml
   volumes:
     - /mnt/pi-nas:/app/pi-storage
   ```

3. **Simulate limited resources:**
   ```bash
   docker run --memory=800m --cpus=0.8 ...
   ```

## Next Steps

Once local testing is successful:
1. Push code to GitHub
2. Follow AWS_EC2_DEPLOYMENT.md
3. Use deploy-to-aws.sh for automatic setup
4. Monitor application on EC2 for 24 hours

## Support Commands

```bash
# View all logs
docker-compose logs

# View specific service logs
docker logs pi-media-server

# Execute command in container
docker exec pi-media-server ls -la /app

# Access container shell
docker exec -it pi-media-server bash

# Copy file from container
docker cp pi-media-server:/app/data/users.json ./

# Inspect container
docker inspect pi-media-server

# View resource usage
docker stats pi-media-server
```

## Quick Reference

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart specific service
docker-compose restart streamlit

# Rebuild image
docker-compose build --no-cache

# Remove volumes (careful - deletes data)
docker-compose down -v
```

---

**Once testing passes locally, you're ready for AWS deployment!** 🚀

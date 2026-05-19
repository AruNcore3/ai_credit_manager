# Billbridge
this is a tool to manage ai token basically it will help an ai powered saas business to manually top up within mid cycle billing

## Redis setup (Step 2)

### Local Redis with Docker
1. Start Redis:
```bash
docker compose -f docker-compose.redis.yml up -d
```
2. Verify Redis is healthy:
```bash
docker compose -f docker-compose.redis.yml ps
```
3. Use this in `.env`:
```env
REDIS_URL=redis://localhost:6379/0
```
4. Stop Redis:
```bash
docker compose -f docker-compose.redis.yml down
```

### Production Redis (managed)
Use a managed Redis provider and set `REDIS_URL` to the provider connection string, for example:
```env
REDIS_URL=redis://<username>:<password>@<host>:<port>/0
```

## Redis rate-limiter rollout (Steps 3-6)

### Step 3: Enable Redis backend
Set:
```env
RATE_LIMIT_BACKEND=redis
```

### Step 4: Key design and scope
- Default key shape: `rl:{api_key}:{window_slot}`
- Optional per-route shape: `rl:{api_key}:{route}:{window_slot}`
- Enable per-route scope with:
```env
RATE_LIMIT_INCLUDE_PATH=true
```

### Step 5: Redis failure strategy
- Fail-open (recommended during initial rollout):
```env
RATE_LIMIT_FAIL_OPEN=true
```
- Fail-closed (strict protection):
```env
RATE_LIMIT_FAIL_OPEN=false
```

### Step 6: Verify
Run tests:
```bash
.venv\Scripts\python.exe -m pytest -q tests
```

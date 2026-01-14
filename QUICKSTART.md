<!--
Copyright 2026 icecake0141
SPDX-License-Identifier: Apache-2.0

This file was created or modified with the assistance of an AI (Large Language Model).
Please review for correctness and security.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
# Quick Start Guide

This guide will help you get the Network Device Configuration Manager up and running quickly.

## Prerequisites

- Docker and Docker Compose installed
- OR Python 3.11+ for local development

## Option 1: Docker Compose (Recommended)

### Start All Services

```bash
# Clone the repository
git clone https://github.com/icecake0141/nw-edit.git
cd nw-edit

# Start services (backend, frontend)
docker-compose up -d

# Optional: start mock SSH server for testing
docker-compose --profile test up -d mock-ssh

# Or use the start script
./start.sh
```

### Access the Application

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Stop Services

```bash
docker-compose down
```

## Option 2: Local Development

### Start Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000

### Start Frontend

In a new terminal:

```bash
cd frontend/public
python -m http.server 3000
```

Frontend will be available at http://localhost:3000

## Using the Application

### Step 1: Import Devices

1. Navigate to the **Device Import** tab
2. Prepare your CSV file with device information:
   ```csv
   host,port,device_type,username,password,name,verify_cmds
   192.168.1.1,22,cisco_ios,admin,password,Router1,show running-config
   ```
3. Paste the CSV content into the text area
4. Click **Import and Validate Devices**
5. Wait for connection validation to complete
6. Only devices that pass connection test will be imported

**Sample CSV**: See `sample_devices.csv` for a complete example

### Step 2: Create a Configuration Job

1. Navigate to the **Create Job** tab
2. Select devices to configure (checkboxes)
3. **Important**: Select one device as the **Canary** (tested first)
4. Enter verification commands (optional):
   ```
   show running-config | section snmp
   show ip interface brief
   ```
5. Enter configuration commands:
   ```
   snmp-server community public RO
   snmp-server location DataCenter1
   ```
6. Configure options:
   - **Verify Mode**: Canary only (default) / All devices / None
   - **Concurrency Limit**: Maximum parallel operations (default: 5)
   - **Stagger Delay**: Delay between device operations (default: 1s)
   - **Stop on Error**: Stop if any device fails (default: true)
7. Click **Create and Execute Job**

**Sample Commands**: See `sample_commands.txt` for examples

### Step 3: Monitor Job Execution

1. You will be automatically redirected to the **Monitor Jobs** tab
2. Watch real-time log streaming for each device
3. View device status (Queued → Running → Success/Failed)
4. After completion, review:
   - **Logs**: Command execution logs
   - **Pre/Post Diff**: Configuration changes
   - **Errors**: Any failures with error messages

## Using the Mock SSH Server

For testing without real devices, use the included mock SSH server:

```bash
# Start mock SSH server
docker-compose --profile test up -d mock-ssh

# Connection details:
# Host: localhost
# Port: 2222
# Username: admin
# Password: admin123
# Device Type: cisco_ios
```

Add to your CSV:
```csv
host,port,device_type,username,password,name,verify_cmds
localhost,2222,cisco_ios,admin,admin123,Mock-Device,show running-config
```

## Troubleshooting

### Backend won't start

- Check if port 8000 is already in use
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check logs: `docker-compose logs backend`

### Frontend won't connect to backend

- Ensure backend is running on port 8000
- Check browser console for errors
- Verify CORS is enabled (already configured)

### Device connection fails

- Verify device is reachable from the server
- Check SSH credentials
- Ensure correct device_type (e.g., cisco_ios, cisco_nxos)
- Check firewall rules

### WebSocket connection fails

- Ensure both frontend and backend are running
- Check that WebSocket URL is correct
- Look for proxy/firewall blocking WebSocket connections

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [API Documentation](http://localhost:8000/docs) (when running)
- See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Review sample files: `sample_devices.csv` and `sample_commands.txt`

## Security Reminders

⚠️ **Important Security Notes:**

- All credentials are stored in memory only (not persisted)
- CSV files contain plaintext passwords - keep them secure
- Use only in trusted, isolated networks
- Not suitable for production without additional security measures
- Never commit CSV files with real credentials to version control

## Getting Help

- Open an issue on GitHub
- Check existing issues for similar problems
- Review the full README for detailed information

# Deployment Blueprint: ConverseNow Ecosystem

This document provides step-by-step production deployment instructions for both the **FastAPI Backend** and the **Unity WebGL Client**.

---

## 1. Deploying the FastAPI Backend (Python)

### Option A: Hosting via Render or Railway (Container-based)
Render and Railway natively support Dockerfiles and will automatically configure SSL (`wss://`) for you.

1. **Push the Code**: Ensure the `Dockerfile` we created is committed and pushed to the root of your GitHub repository.
2. **Create Web Service**:
   * Log into [Render](https://render.com) or [Railway](https://railway.app).
   * Create a new **Web Service** and connect it to your GitHub repository.
3. **Environment Variables**:
   * Add `SARVAM_API_KEY`: Your subscription key for SarvamAI translation.
   * Add `WHISPER_MODEL`: (Optional, defaults to `small`). Set to `tiny` or `base` if deploying to a low-compute free tier to minimize latency.
4. **Deploy**: The platform will read the `Dockerfile`, install system-level `ffmpeg` (required for Whisper), install python dependencies, and launch Uvicorn.
5. **Get Endpoint**: You will receive a secure URL like `https://your-app-name.onrender.com`. Replace `https://` with `wss://` for Unity configuration (e.g., `wss://your-app-name.onrender.com/ws/audio`).

---

### Option B: Hosting on a Linux VM (AWS EC2 / DigitalOcean / GCP)
This option is recommended if you want to deploy onto a GPU-enabled VM (e.g. AWS `g4dn.xlarge` with an NVIDIA T4 GPU) to run Whisper in sub-second times.

#### 1. Setup the Server Environment
Connect to your VM via SSH and run:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv ffmpeg git nginx
```

#### 2. Clone and Setup Repository
```bash
git clone https://github.com/AdityaThakur193/ConverseNow-backend.git
cd ConverseNow-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 3. Run Backend as a Systemd Service
Create a systemd unit file to keep the backend running:
```bash
sudo nano /etc/systemd/system/conversenow.service
```
Paste the following configuration:
```ini
[Unit]
Description=ConverseNow FastAPI Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/ConverseNow-backend
ExecStart=/home/ubuntu/ConverseNow-backend/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
Environment=SARVAM_API_KEY=your_key_here
Environment=WHISPER_MODEL=small

[Install]
WantedBy=multi-user.target
```
Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable conversenow
sudo systemctl start conversenow
```

#### 4. Configure Nginx Reverse Proxy with SSL (WSS Support)
Create an Nginx configuration file:
```bash
sudo nano /etc/nginx/sites-available/conversenow
```
Paste this configuration:
```nginx
server {
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Link the file and reload Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/conversenow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```
Obtain a free SSL certificate using Let's Encrypt / Certbot:
```bash
sudo apt install snapd
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
sudo certbot --nginx -d api.yourdomain.com
```
Certbot will configure Nginx automatically. Your backend will now be securely accessible at `wss://api.yourdomain.com/ws/audio`.

---

## 2. Deploying the Unity Client (WebGL)

WebGL is the easiest way for public users to access your Unity frontend.

1. **Unity Setup**:
   * Open the project in Unity.
   * Go to **File -> Build Settings**.
   * Switch the Platform to **WebGL**.
   * Open the Player Settings and under **Publishing Settings**, ensure **Decompression Fallback** is checked (this makes loading faster on standard hosts).
2. **Point to Cloud Backend**:
   * Locate the `AudioStreamer` script attached to your scene's managers.
   * In the inspector, change the `backendUrl` from `ws://localhost:8000/ws/audio` to your new cloud WebSocket URL: `wss://api.yourdomain.com/ws/audio` (or your Render/Railway `wss://` address).
3. **Compile Build**:
   * Click **Build** and choose an empty output directory. Unity compiles the project into an HTML page and a folder containing WASM binary assets.
4. **Deploy static files**:
   * Deploy the build folder to **GitHub Pages** (free), **Vercel** (free), or **Netlify**.
   * When users open the page in their browser, they will see the 3D avatar and can speak directly into their device microphone to trigger translations.

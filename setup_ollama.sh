#!/bin/bash
echo "🚀 Configuring Ollama Network..."

# 1. Force Ollama to listen on all interfaces (0.0.0.0)
# We override the systemd service config
sudo mkdir -p /etc/systemd/system/ollama.service.d
echo '[Service]' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
echo 'Environment="OLLAMA_HOST=0.0.0.0"' | sudo tee -a /etc/systemd/system/ollama.service.d/override.conf

# 2. Open the Firewall (UFW) for port 11434
if command -v ufw >/dev/null; then
    echo "🔓 Opening Firewall Port 11434..."
    sudo ufw allow 11434/tcp
    sudo ufw reload
fi

# 3. Restart Ollama to apply changes
echo "🔄 Restarting Ollama..."
sudo systemctl daemon-reload
sudo systemctl restart ollama

echo "✅ Success! Ollama is now listening on 0.0.0.0:11434"
echo "You can now run 'streamlit run app.py' inside Daytona."
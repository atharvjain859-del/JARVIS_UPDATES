# OpenSSH / SFTP file access (approval-gated)

This is an optional capability. Do not install or enable it automatically.

## What it does

OpenSSH Server lets you connect from another computer on the same trusted network using SSH or SFTP. It does not send files through email, WhatsApp, or a cloud messaging service. For access from outside your home network, use a private VPN such as Tailscale; do not expose port 22 directly to the public internet.

## Windows host setup

1. On the PC that holds the files, open **Settings → System → Optional features → View features**.
2. Install **OpenSSH Server**. (The client alone is not sufficient to accept incoming connections.)
3. Open PowerShell as Administrator and run:

```powershell
Get-Service sshd
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
```

4. Ensure Windows Firewall permits OpenSSH Server only on trusted/private networks. Avoid creating a public internet port-forward.
5. Find the host's LAN IP with `ipconfig`. From the other PC, connect using:

```powershell
ssh WINDOWS_USERNAME@HOST_LAN_IP
sftp WINDOWS_USERNAME@HOST_LAN_IP
```

6. Use `get` / `put` in the SFTP prompt to transfer files. Use a standard, non-admin Windows account with access limited to the folders you intend to share. Prefer SSH keys; protect the private key and never put credentials in JARVIS logs or the updater manifest.

## Remote access

For access when the PCs are on different networks, connect both to a private VPN such as Tailscale first, then use the host's VPN IP. Do not expose SSH directly to the public internet.

## Safety / approval

Enabling `sshd`, changing startup settings, and adding firewall rules are system-level changes. JARVIS must explain the change and obtain explicit user approval before doing them. This guide alone performs no installation, service, firewall, or network changes.

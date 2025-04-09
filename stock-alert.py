import requests
import json
import smtplib
import os
import time
from email.mime.text import MIMEText
from datetime import datetime

# File paths
CONFIG_FILE = "config.json"
WATCHLIST_FILE = "watchlist.json"
ALERT_LOG_FILE = "alerts.log"

def load_config():
    # Try to load config or create a template if it doesn't exist
    if not os.path.exists(CONFIG_FILE):
        print(f"Config file not found. Creating a template at {CONFIG_FILE}")
        print("Please edit it with your details and restart.")
        
        template = {
            "API_KEY": "your_alphavantage_api_key",
            "EMAIL": "your_email@example.com",
            "EMAIL_PASSWORD": "your_app_password",
            "SMTP_SERVER": "smtp.gmail.com",
            "SMTP_PORT": 465
        }
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(template, f, indent=2)
        exit(1)
        
    # Load and validate config
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    
    # Check required fields
    missing = []
    for field in ["API_KEY", "EMAIL", "EMAIL_PASSWORD", "SMTP_SERVER", "SMTP_PORT"]:
        if field not in config or not config[field]:
            missing.append(field)
    
    if missing:
        print(f"Missing config values: {', '.join(missing)}")
        print(f"Please update your {CONFIG_FILE}")
        exit(1)
        
    return config

def get_current_price(symbol, api_key):
    """Get the latest stock price from Alpha Vantage"""
    url = f"https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "1min",
        "apikey": api_key
    }
    
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        # Check for API errors
        if "Error Message" in data:
            print(f"API error for {symbol}: {data['Error Message']}")
            return None
            
        # Check for rate limit message
        if "Note" in data and "call frequency" in data["Note"]:
            print(f"Hit API rate limit. Waiting 60 seconds...")
            time.sleep(60)
            return None
            
        # Get latest price
        time_series = data.get("Time Series (1min)", {})
        if not time_series:
            print(f"No data returned for {symbol}")
            return None
            
        # Find the most recent data point
        latest_time = sorted(time_series.keys())[-1]
        price = float(time_series[latest_time]["1. open"])
        
        return price
        
    except requests.exceptions.Timeout:
        print(f"Request timed out for {symbol}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {symbol}: {e}")
    except (KeyError, ValueError) as e:
        print(f"Data error for {symbol}: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    return None

def load_watchlist():
    """Load the watchlist from disk"""
    if not os.path.exists(WATCHLIST_FILE):
        return []
        
    try:
        with open(WATCHLIST_FILE) as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("Watchlist file corrupted, creating new one")
        return []

def save_watchlist(stocks):
    """Save the watchlist to disk"""
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(stocks, f, indent=2)

def send_alert(symbol, price, target, direction, config):
    """Send an email alert when price conditions are met"""
    subject = f"Stock Alert: {symbol} ${price:.2f}"
    
    # Create a more informative message body
    body = f"""
STOCK PRICE ALERT

Symbol: {symbol}
Current Price: ${price:.2f}
Target: ${target:.2f} ({direction})
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated alert from your Stock Price Alert system.
"""

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = config['EMAIL']
    msg['To'] = config['EMAIL']
    
    try:
        server = smtplib.SMTP_SSL(config['SMTP_SERVER'], config['SMTP_PORT'])
        server.login(config['EMAIL'], config['EMAIL_PASSWORD'])
        server.send_message(msg)
        server.close()
        
        # Log the alert
        with open(ALERT_LOG_FILE, "a") as log:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log.write(f"[{timestamp}] ALERT: {symbol} at ${price:.2f} (target: ${target:.2f} {direction})\n")
            
        print(f"✓ Alert sent for {symbol}")
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def display_watchlist(stocks):
    """Show the watchlist in a nicely formatted table"""
    if not stocks:
        print("Your watchlist is empty")
        return
        
    # Calculate column widths based on content
    headers = ["Symbol", "Target", "Direction", "Status", "Added"]
    
    print("\nWatchlist:")
    print("─" * 65)
    print(f"{headers[0]:<8} {headers[1]:<10} {headers[2]:<10} {headers[3]:<10} {headers[4]}")
    print("─" * 65)
    
    for stock in stocks:
        status = "ALERTED" if stock.get('alerted') else "watching"
        added_date = stock.get('added', 'unknown')
        print(f"{stock['symbol']:<8} ${stock['target']:<9.2f} {stock['direction']:<10} {status:<10} {added_date}")
    
    print("─" * 65)
    print(f"Total: {len(stocks)} stocks\n")

def check_prices(stocks, config):
    """Check current prices against targets for all stocks"""
    if not stocks:
        print("Watchlist is empty. Add stocks first.")
        return
    
    changes = False
    print(f"Checking prices for {len(stocks)} stocks...")
    
    for i, stock in enumerate(stocks):
        # Skip if already alerted
        if stock.get('alerted'):
            print(f"{stock['symbol']}: Already triggered, use 'reset' to check again")
            continue
            
        # Add delay between API calls to respect rate limits
        if i > 0:
            time.sleep(12)  # Alpha Vantage free tier allows 5 calls per minute
        
        # Get current price
        price = get_current_price(stock['symbol'], config['API_KEY'])
        if price is None:
            continue
            
        # Check if alert conditions are met
        target = stock['target']
        direction = stock['direction']
        
        if (direction == 'above' and price >= target) or (direction == 'below' and price <= target):
            # Send the alert
            if send_alert(stock['symbol'], price, target, direction, config):
                stock['alerted'] = True
                changes = True
        else:
            print(f"{stock['symbol']}: ${price:.2f} (target: ${target:.2f} {direction})")
    
    # Save any changes to watch status
    if changes:
        save_watchlist(stocks)

def main():
    # Setup and initialization
    print("\n╔═══════════════════════════════╗")
    print("║     STOCK PRICE ALERT TOOL    ║")
    print("╚═══════════════════════════════╝\n")
    
    # Load config
    try:
        config = load_config()
        print("Configuration loaded successfully")
    except Exception as e:
        print(f"Config error: {e}")
        return
    
    # Load watchlist
    watchlist = load_watchlist()
    
    # Command prompt
    commands = {
        "add": "Add a stock to your watchlist",
        "remove": "Remove a stock from your watchlist",
        "list": "Display your watchlist", 
        "check": "Check current prices against targets",
        "reset": "Reset triggered alerts",
        "help": "Show available commands",
        "quit": "Exit the program"
    }
    
    print("\nType 'help' to see available commands\n")
    
    while True:
        try:
            cmd = input("> ").strip().lower()
            
            if cmd == "help":
                print("\nAvailable commands:")
                for c, desc in commands.items():
                    print(f"  {c:<6} - {desc}")
                    
            elif cmd == "add":
                # Get stock info
                symbol = input("Symbol: ").strip().upper()
                if not symbol or not symbol.isalnum():
                    print("Invalid symbol")
                    continue
                
                # Check if already in watchlist
                if any(s['symbol'] == symbol for s in watchlist):
                    print(f"{symbol} is already in your watchlist")
                    continue
                
                # Get target price
                try:
                    target = float(input("Target price: $").strip())
                except ValueError:
                    print("Invalid price - must be a number")
                    continue
                
                # Get direction
                direction = input("Direction (above/below): ").strip().lower()
                if direction not in ["above", "below"]:
                    print("Direction must be 'above' or 'below'")
                    continue
                
                # Add to watchlist
                watchlist.append({
                    "symbol": symbol,
                    "target": target,
                    "direction": direction,
                    "alerted": False,
                    "added": datetime.now().strftime("%Y-%m-%d")
                })
                save_watchlist(watchlist)
                print(f"Added {symbol} to watchlist")
                
            elif cmd == "remove":
                symbol = input("Symbol to remove: ").strip().upper()
                
                # Find and remove from watchlist
                before_len = len(watchlist)
                watchlist = [s for s in watchlist if s['symbol'] != symbol]
                
                if len(watchlist) < before_len:
                    save_watchlist(watchlist)
                    print(f"Removed {symbol} from watchlist")
                else:
                    print(f"{symbol} not found in watchlist")
                    
            elif cmd == "list":
                display_watchlist(watchlist)
                
            elif cmd == "check":
                check_prices(watchlist, config)
                
            elif cmd == "reset":
                # Reset all alerts
                changes = False
                for stock in watchlist:
                    if stock.get('alerted'):
                        stock['alerted'] = False
                        changes = True
                
                if changes:
                    save_watchlist(watchlist)
                    print("All alerts have been reset")
                else:
                    print("No triggered alerts to reset")
                    
            elif cmd == "quit" or cmd == "exit":
                print("Goodbye!")
                break
                
            else:
                print(f"Unknown command: '{cmd}'")
                print("Type 'help' to see available commands")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
# chicken.gg checker

Multithreaded python account checker for chicken.gg. It automatically solves cloudflare turnstile captchas in the background using camoufox (a headless firefox implementation) and pulls full account statistics.

It captures balance, wager amount, level, and all available rakeback rewards (quick, daily, weekly, monthly, and rankup).

### Features
- automated turnstile captcha solver
- multithreaded login checking
- detailed console ui with live stats (valid, invalid, errors)
- proxy support
- saves valid hits cleanly to a text file

### prerequisites
Python 3.10 or higher.

### installation

1. Clone the repository or download the files.
2. Open a terminal in the folder and install the required python packages:

    pip install -r requirements.txt

3. Install the camoufox browser environment:

    python -m camoufox fetch

### Setup

Before running the checker, you need to set up your proxies and combo list.

Proxies:
create a file named proxies.txt in the same directory as the script. paste your proxies inside, one per line. the script supports standard formats:
- ip:port
- ip:port:user:pass
- http://ip:port
- http://user:pass@ip:port

Accounts:
have a combo file ready (e.g., combo.txt) with your accounts formatted as username:password per line.

### Usage

Run the script from your terminal:

    python checker.py

The script will prompt you for a few things:
1. Accounts file: type the name of your combo file (e.g., combo.txt) and press enter.
2. Threads: how many concurrent login checks to run. default is 16 (maximum is capped at 24).
3. Solver slots: the number of browser instances to keep open for solving captchas. default is 20. be careful going over 16 slots if you have low ram, as each solver instance spawns a browser context that consumes system memory.
4. Retries: the number of times an account can retry in case of an unexpected error or block (for example if the connection drops).

Once it starts, it will cycle through your proxies automatically. valid hits are printed to the console and appended to valid.txt in the same folder.

### Output format
When an account hits, it saves to valid.txt like this:

    username:password | Balance = 5.50 | Wagered = 1050.00 | Level = 22 | Quick = 0.0500 | Daily = 0.1000 | Weekly = 0.5000 | Monthly = 1.2500 | RankUp = 0.0000

### Notes
- If you get a lot of errors, your proxies are either dead or getting blocked. Rotating proxies are the best for this script, as no proper cloudflare proxying has been yet implemented and static IPs will get flagged quickly.
- The captcha solver runs headless (invisible). If you need to debug it, you can edit the script and change "headless=True" to "headless=False".

### Critical info:
- No proxying system has been yet implemented to the cloudflare solver, this is one of the major speed bottlencks.

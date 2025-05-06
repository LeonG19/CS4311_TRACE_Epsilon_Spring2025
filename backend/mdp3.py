import random
import re
import math
import unicodedata
from collections import defaultdict
from typing import Dict, List, Tuple, Set
import csv
import os
import time
import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp

# Global stop flag
def stop_generation():
    return False

# NLP routine: normalize text to ASCII and retain only letters, digits, and common symbols
def nlp_subroutine(csv_path: str):
    """
    Reads a CSV with columns id, content, url; cleans content by:
      1. ASCII-normalizing (remove non-English chars)
      2. Splitting hyphenated compounds
      3. Removing definite, demonstrative, distributive, and interrogative determiners
      4. Removing possessive determiners (with a simple title-case exception)
      5. Dropping all tokens <4 chars unless they’re acronyms
    """
    # 1. Define determiner sets
    DETERMINERS = {
        "the",            # definite
        "this","that","these","those",           # demonstrative
        "each","every","either","neither",       # distributive
        "which","what","whose"                   # interrogative
    }
    POSSESSIVES = {"my","your","his","her","its","our","their"}

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    cleaned_rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        if not {"id","content","url"}.issubset(fields):
            raise ValueError("CSV must contain id, content, url")

        for row in reader:
            raw = row.get("content","") or ""

            # 2. Unicode → ASCII (strip accents & non-ASCII)
            text = unicodedata.normalize("NFKD", raw)
            text = text.encode("ascii", "ignore").decode("ascii")

            # 3. Split hyphenated compounds (sister-in-law → sister in law)
            text = re.sub(r"(?<=\w)-(?=\w)", " ", text)

            # 4. Tokenize on non-word boundaries (keep letters, digits, & & .)
            tokens = re.findall(r"[A-Za-z0-9&\.]+", text)

            out_tokens = []
            for i, tok in enumerate(tokens):
                low = tok.lower()

                # a) Remove those determiners
                if low in DETERMINERS:
                    continue

                # b) Remove possessive determiners, except if next token is TitleCase
                if low in POSSESSIVES:
                    nxt = tokens[i+1] if i+1 < len(tokens) else ""
                    if not re.match(r"[A-Z]", nxt):
                        continue

                # c) Length <4? keep only if all-caps acronym (≥2 letters)
                if len(tok) < 4:
                    # acronym e.g. NASA, H.P. (no digits)
                    stripped = tok.replace(".","").replace("&","")
                    if not (stripped.isupper() and len(stripped) >= 2 and stripped.isalpha()):
                        continue

                out_tokens.append(tok)

            row["content"] = " ".join(out_tokens)
            cleaned_rows.append(row)

    # 5. Overwrite CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(cleaned_rows)

# Load URLs from CSV
def load_urls_from_csv(path: str) -> List[str]:
    if not os.path.exists(path): raise FileNotFoundError(path)
    urls: List[str] = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not {'id','website'}.issubset(reader.fieldnames or []): raise ValueError
        for r in reader:
            if r['website']:
                urls.append(r['website'].strip())
    return urls

# Web scraper
class WebScraper:
    def __init__(
        self,
        urls: List[str],
        batch_size: int = 20,
        concurrency: int = 5
    ):
        self.urls = urls
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(concurrency)

    async def _fetch(self, session: aiohttp.ClientSession, url: str) -> str:
        async with self.semaphore:
            async with session.get(url, timeout=10) as resp:
                resp.raise_for_status()
                return await resp.text()

    async def _parse(self, html: str) -> Tuple[str, str, str, str]:
        soup = BeautifulSoup(html, 'html.parser')

        text = ' '.join(tag.get_text(strip=True)
                        for tag in soup.find_all(['p','h1','h2','h3','span']))
        logos = ' '.join(img['alt'].strip()
                         for img in soup.find_all('img', alt=True))
        labels = ' '.join(lbl.get_text(strip=True)
                          for lbl in soup.find_all('label'))
        classes = ' '.join(
            cls
            for elem in soup.find_all(class_=True)
            for cls in elem.get('class', [])
        )
        return text, logos, labels, classes  # :contentReference[oaicite:6]{index=6}

    async def _scrape(self, session: aiohttp.ClientSession, url: str) -> Tuple[str,str,str,str,str]:
        html = await self._fetch(session, url)
        text, logos, labels, classes = await self._parse(html)
        return url, text, logos, labels, classes

    async def _process_batch(self, batch: List[str]) -> List[Tuple[str,str,str,str,str]]:
        async with aiohttp.ClientSession() as session:
            tasks = [self._scrape(session, url) for url in batch]
            results = []
            for coro in asyncio.as_completed(tasks):
                try:
                    row = await coro
                    results.append(row)
                except Exception:
                    continue
            return results  # :contentReference[oaicite:7]{index=7}

    async def generate_csv(self, output_path: str = "web_text.csv"):
        """
        Scrape all URLs in batches, then write a single CSV:
            id, content, url

        content = text + logos + labels + classes
        """
        all_rows: List[Tuple[int, str, str]] = []
        total = len(self.urls)

        # 1) Fetch in batches
        for i in range(0, total, self.batch_size):
            batch = self.urls[i : i + self.batch_size]
            rows = await self._process_batch(batch)

            # 2) Collapse each row’s pieces into a single 'content' string
            for idx, (url, text, logos, labels, classes) in enumerate(rows, start=i+1):
                parts = [text, logos, labels, classes]
                # join non-empty bits with a space
                content = " ".join(p for p in parts if p)
                all_rows.append((idx, content, url))

        # 3) Write the single CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'content', 'url'])
            writer.writerows(all_rows)

        print(f"Wrote {len(all_rows)} records to {output_path}")
# Load web text
def load_web_text(csv_path: str) -> str:
    if not os.path.exists(csv_path): raise FileNotFoundError(csv_path)
    out: List[str] = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        rdr = csv.DictReader(f)
        if not {'id','content','url'}.issubset(rdr.fieldnames or []): raise ValueError
        for r in rdr:
            if r['content']:
                out.append(r['content'].lower())
    return ' '.join(out)

# Load wordlist
def load_wordlist(fp: str) -> List[str]:
    if not os.path.exists(fp): raise FileNotFoundError(fp)
    with open(fp, 'r', encoding='utf-8') as f:
        return [l.strip().lower() for l in f if l.strip()]

# Credential MDP core
class CredentialMDP:
    def __init__(self, order: int = 2, gamma: float = 0.9):
        self.order = order
        self.gamma = gamma
        self.initial_gamma = gamma
        self.gamma_increment = (0.99 - gamma) / 10000.0
        self.epsilon0 = 1.0
        self.min_eps = 0.01
        self.eps_decay = math.log(2) / 50
        self.steps = 0
        self.update_cnt = 0
        self.q: Dict[str, Dict[Tuple[str, str], float]] = defaultdict(lambda: defaultdict(float))
        self.trans: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        self.init_states: List[str] = []

    def calc_pwd(self, pwd: str) -> float:
        s = 0.0
        if len(pwd) >= 12: s += 0.25
        if re.search(r'[!@#$%^&*]', pwd): s += 0.25
        if len(set(pwd)) >= 8: s += 0.20
        if re.search(r'\d', pwd): s += 0.15
        if re.search(r'[A-Z]', pwd): s += 0.15
        return s

    def calc_user(self, user: str) -> float:
        reserved = {'admin', 'root'}
        score = 0.0
        # Uniqueness
        score += 0.50
        # Length
        if len(user) >= 6: score += 0.20
        # Starts with letter
        if re.match(r'^[A-Za-z]', user): score += 0.20
        # Penalize obvious names
        if user.lower() in reserved: score -= 0.10
        return score

    def get_reward(self, state: str, action: str, ch: str) -> float:
        typ = 'username' if state.startswith('username') else 'password'
        curr = state.split('_', 1)[1] + ch
        base = (self.calc_user(curr) if typ == 'username' else self.calc_pwd(curr)) / len(curr)
        bonus = 0.0
        if typ == 'username' and ch.isdigit(): bonus += 0.10
        if re.search(r'[!@#$%^&*]', ch): bonus += 0.10
        return base + bonus

    def actions(self, state: str) -> List[str]:
        return list(self.trans[state].keys())

    def choose_action(self, state: str) -> Tuple[str, str]:
        self.steps += 1
        eps = max(self.min_eps, self.epsilon0 * math.exp(-self.eps_decay * self.steps))
        # update gamma
        self.gamma = min(0.99, self.gamma + self.gamma_increment)
        possible = self.actions(state)
        if not possible:
            return "", ""
        if random.random() < eps:
            act = random.choice(possible)
            nxt = random.choice(list(self.trans[state][act]))
        else:
            values = {act: max(self.q[state][(act, nxt)] for nxt in self.trans[state][act]) for act in possible}
            act = max(values, key=values.get)
            nxt = random.choice(list(self.trans[state][act]))
        return act, nxt

    def update_q(self, state: str, action: str, nxt: str, next_state: str, reward: float):
        self.update_cnt += 1
        alpha = 1 / math.sqrt(1 + self.update_cnt)
        next_vals = [self.q[next_state][(act, c)] for act in self.actions(next_state) for c in self.trans[next_state][act]] or [0]
        self.q[state][(action, nxt)] += alpha * (reward + self.gamma * max(next_vals) - self.q[state][(action, nxt)])

# Generator class
class CredentialGeneratorMDP:
    def __init__(
        self,
        csv_path: str,
        wl_path: str,
        u_c: bool,
        u_n: bool,
        u_s: bool,
        u_len: int,
        p_c: bool,
        p_n: bool,
        p_s: bool,
        p_len: int
    ):
        try:
            self.text = load_web_text(csv_path)
        except:
            self.text = ""
        try:
            self.words = load_wordlist(wl_path)
        except:
            self.words = []
        self.u_c, self.u_n, self.u_s = u_c, u_n, u_s
        self.p_c, self.p_n, self.p_s = p_c, p_n, p_s
        if u_len < 12:
            u_order = 3
        else:
            u_order = 4
        if p_len < 12:
            p_order = 2
        else:
            p_order = 3
       
       
        self.umdp = CredentialMDP(order=u_order)
        self.pmdp = CredentialMDP(order=p_order)
        self.min_ul = u_len
        self.min_pl = p_len
        self.usyms = set('!@#$%^&*()-_=+[]{}|;:\".<>/?~`')
        self.psyms = self.usyms

    def allow_u(self, ch: str) -> bool:
        return (ch.isalpha() and self.u_c) or (ch.isdigit() and self.u_n) or (ch in self.usyms and self.u_s)

    def allow_p(self, ch: str) -> bool:
        return (ch.isalpha() and self.p_c) or (ch.isdigit() and self.p_n) or (ch in self.psyms and self.p_s)

    def chars_u(self) -> str:
        s = ''
        if self.u_c: s += 'abcdefghijklmnopqrstuvwxyz'
        if self.u_n: s += '0123456789'
        if self.u_s: s += ''.join(self.usyms)
        return s

    def chars_p(self) -> str:
        s = ''
        if self.p_c: s += 'abcdefghijklmnopqrstuvwxyz'
        if self.p_n: s += '0123456789'
        if self.p_s: s += ''.join(self.psyms)
        return s

    def preprocess(self, text: str) -> List[str]:
        return [w for w in re.findall(r'\w+', text.lower()) if len(w) >= 4]

    def build_state_transitions(self):
        self.umdp.trans.clear(); self.umdp.init_states.clear()
        self.pmdp.trans.clear(); self.pmdp.init_states.clear()
        base = set(self.preprocess(self.text)) | set(self.words)
        # Username transitions
        for w in base:
            for i in range(len(w) - self.umdp.order):
                c = w[i + self.umdp.order]
                if not self.allow_u(c): continue
                pref = w[i:i + self.umdp.order]
                state_sub = ''.join('#' if ch in self.usyms else ch for ch in pref)
                state = f"username_{state_sub}"
                self.umdp.trans[state][c].add(c)
                if i == 0 and all(self.allow_u(ch) for ch in pref):
                    self.umdp.init_states.append(state)
        # Fallback
        allowed_u = self.chars_u()
        if not self.umdp.init_states:
            prefix = (allowed_u[0]*self.umdp.order) if allowed_u else 'a'*self.umdp.order
            self.umdp.init_states.append(f"username_{prefix}")
        # Password transitions
        pwd_base = {w for w in base if len(w) >= 8 or w.isdigit()}
        for w in pwd_base:
            for i in range(len(w) - self.pmdp.order):
                c = w[i + self.pmdp.order]
                if not self.allow_p(c): continue
                pref = w[i:i + self.pmdp.order]
                state_sub = ''.join('#' if ch in self.psyms else ch for ch in pref)
                state = f"password_{state_sub}"
                self.pmdp.trans[state][c].add(c)
                if i == 0 and all(self.allow_p(ch) for ch in pref):
                    self.pmdp.init_states.append(state)
        allowed_p = self.chars_p()
        if not self.pmdp.init_states:
            prefix = (allowed_p[0]*self.pmdp.order) if allowed_p else '0'*self.pmdp.order
            self.pmdp.init_states.append(f"password_{prefix}")

    def generate_credential(self) -> Tuple[str, str]:
        # --- PASSWORD GENERATION ---
        # pick a valid seed
        state = random.choice(self.pmdp.init_states)
        pwd = state.split('_', 1)[1]

        # grow to min_pl, always using only allowed chars
        while len(pwd) < self.min_pl:
            act, nxt = self.pmdp.choose_action(state)
            if not act:
                # fallback: choose from exactly the allowed pool for passwords
                pool = self.chars_p()
                nxt  = random.choice(list(pool)) if pool else 'a'
            next_state = f"password_{pwd[-self.pmdp.order:]}"
            r = self.pmdp.get_reward(state, act, nxt)
            self.pmdp.update_q(state, act, nxt, next_state, r)
            pwd += nxt
            state = next_state

        # strip disallowed digits/symbols if flags are off
        if not self.p_n:
            pwd = ''.join(ch for ch in pwd if not ch.isdigit())
        if not self.p_s:
            pwd = ''.join(ch for ch in pwd if ch not in self.psyms)

        # refill to min_pl if stripping dropped length
        pool = self.chars_p()
        while len(pwd) < self.min_pl:
            pwd += random.choice(list(pool)) if pool else 'a'

        # --- USERNAME GENERATION ---
        state = random.choice(self.umdp.init_states)
        user = state.split('_', 1)[1]

        while len(user) < self.min_ul:
            act, nxt = self.umdp.choose_action(state)
            if not act:
                pool = self.chars_u()
                nxt  = random.choice(list(pool)) if pool else 'a'
            next_state = f"username_{user[-self.umdp.order:]}"
            r = self.umdp.get_reward(state, act, nxt)
            self.umdp.update_q(state, act, nxt, next_state, r)
            user += nxt
            state = next_state

        # strip disallowed digits/symbols if flags are off
        if not self.u_n:
            user = ''.join(ch for ch in user if not ch.isdigit())
        if not self.u_s:
            user = ''.join(ch for ch in user if ch not in self.usyms)

        # refill to min_ul if stripping dropped length
        pool = self.chars_u()
        while len(user) < self.min_ul:
            user += random.choice(list(pool)) if pool else 'a'

        return user, pwd

    def generate_credentials(self, count: int = 10) -> List[Tuple[str, str]]:
        self.build_state_transitions()
        creds: List[Tuple[str, str]] = []
        for _ in range(count):
            creds.append(self.generate_credential())
        return creds

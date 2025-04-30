import random
import re
import math
from collections import defaultdict
import numpy as np
from typing import Dict, List, Tuple, Set, Union
import csv
import os
import time
import requests
from bs4 import BeautifulSoup

# Global stop flag
stop_generation = False

import random
import re
import math
import unicodedata
from collections import defaultdict
import numpy as np
from typing import Dict, List, Tuple, Set, Union
import csv
import os
import time
import requests
from bs4 import BeautifulSoup

# Global stop flag
stop_generation = False

# NLP routine: normalize text to ASCII and retain only letters, digits, and common symbols
def nlp_subroutine(csv_path: str):
    stopwords = {"the", "and", "or"}
    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)
    cleaned_rows = []
    with open(csv_path, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        if not fieldnames or not {"id", "content", "url"}.issubset(fieldnames):
            raise ValueError("CSV must contain id,content,url")
        for row in reader:
            raw = row.get('content', '') or ''
            # Normalize to ASCII, stripping accents and non-ASCII chars
            normalized = unicodedata.normalize('NFKD', raw)
            ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
            # Extract only letters, digits, and common symbols
            parts = re.findall(r"[A-Za-z0-9!@#$%^&*()\-_=+\[\]{}|;:'\",.<>/?~`]+", ascii_text)
            filtered = [w for w in parts if w.lower() not in stopwords]
            row['content'] = ' '.join(filtered)
            cleaned_rows.append(row)
    with open(csv_path, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)
    print(f"Cleaned CSV '{csv_path}' file has been generated.")

# Load URLs from a CSV file
def load_urls_from_csv(path: str) -> List[str]:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    urls = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not {'id', 'website'}.issubset(reader.fieldnames or []):
            raise ValueError
        for r in reader:
            if r['website']:
                urls.append(r['website'].strip())
    return urls

# Web scraper
class WebScraper:
    def __init__(self, urls: List[str]):
        self.urls = urls

    def scrape_pages(self) -> List[Tuple[int, str, str]]:
        results = []
        for i, u in enumerate(self.urls, 1):
            if stop_generation:
                break
            try:
                r = requests.get(u, timeout=10)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, 'html.parser')
                text = ' '.join(t.get_text() for t in soup.find_all(['p', 'h1', 'h2', 'h3', 'span']))
                results.append((i, text, u))
                time.sleep(1)
            except Exception:
                pass
        return results

    def generate_csv(self, fn: str):
        data = self.scrape_pages()
        with open(fn, 'w', newline='', encoding='utf-8') as c:
            writer = csv.writer(c)
            writer.writerow(['id', 'content', 'url'])
            writer.writerows(data)

# Load web text

def load_web_text(csv_path: str) -> str:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)
    out = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not {'id', 'content', 'url'}.issubset(reader.fieldnames or []):
            raise ValueError
        for r in reader:
            if r['content']:
                out.append(r['content'].lower())
    return ' '.join(out)

# Load wordlist

def load_wordlist(fp: str) -> List[str]:
    if not os.path.exists(fp):
        raise FileNotFoundError(fp)
    with open(fp, 'r', encoding='utf-8') as f:
        return [l.strip().lower() for l in f if l.strip()]

# (Remaining MDP core and generator classes unchanged ...)


# Credential MDP core
class CredentialMDP:
    def __init__(self, order: int = 2, gamma: float = 0.9):
        self.order = order
        self.gamma0 = gamma
        self.gamma = gamma
        # Exploration parameters (ε decay)
        self.epsilon0 = 1.0
        self.min_epsilon = 0.01
        self.epsilon_decay_lambda = math.log(2) / 50
        self.step_count = 0
        self.epsilon = self.epsilon0
        # Learning rate parameters
        self.update_count = 0
        self.learning_rate0 = 0.1
        # Q-values and transitions
        self.q_values: Dict[str, Dict[Tuple[str, str], float]] = defaultdict(lambda: defaultdict(float))
        self.state_transitions: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        self.initial_states: List[str] = []

    def calculate_password_strength(self, password: str) -> float:
        score = 0.0
        if len(password) >= 12:
            score += 0.25
        if re.search(r'[!@#$%^&*]', password):
            score += 0.25
        if len(set(password)) >= 8:
            score += 0.20
        if re.search(r'[0-9]', password):
            score += 0.15
        if re.search(r'[A-Z]', password):
            score += 0.15
        return score

    def calculate_username_quality(self, username: str) -> float:
        reserved = {'admin', 'root'}
        score = 0.0
        if username not in self.q_values:
            score += 0.50
        if len(username) >= 6:
            score += 0.20
        if re.match(r'^[a-zA-Z]', username):
            score += 0.20
        if re.search(r'[0-9]', username):
            score += 0.10
        if username.lower() in reserved:
            score -= 0.10
        return score

    def get_reward(self, state: str, action: str, next_char: str) -> float:
        # Base reward
        if 'username' in state:
            current = state.split('_', 1)[1] + next_char
            base = self.calculate_username_quality(current) / len(current)
        else:
            current = state.split('_', 1)[1] + next_char
            base = self.calculate_password_strength(current) / len(current)
        # Potential-based shaping for symbols
        symbol_set = set('!@#$%^&*')
        phi_prime = 1 if (next_char in symbol_set and (len(current) <= 2 or len(current) >= self.order + 1)) else 0
        shaping = phi_prime * 0.05
        # Additional shaping for digits in usernames
        if 'username' in state and next_char.isdigit():
            shaping += 0.05
        return base + shaping

    def get_possible_actions(self, state: str) -> List[str]:
        return list(self.state_transitions[state].keys())

    def choose_action(self, state: str) -> Tuple[str, str]:
        self.step_count += 1
        self.epsilon = max(self.min_epsilon, self.epsilon0 * math.exp(-self.epsilon_decay_lambda * self.step_count))
        self.gamma = min(0.99, self.gamma + 1e-4)
        possible = self.get_possible_actions(state)
        if not possible:
            return "", ""
        if random.random() < self.epsilon:
            action = random.choice(possible)
            next_char = random.choice(list(self.state_transitions[state][action]))
        else:
            values = {a: max(self.q_values[state][(a, c)] for c in self.state_transitions[state][a]) for a in possible}
            action = max(values, key=values.get)
            next_char = random.choice(list(self.state_transitions[state][action]))
        return action, next_char

    def update_q_value(self, state: str, action: str, next_char: str, next_state: str, reward: float):
        self.update_count += 1
        alpha = 1 / math.sqrt(1 + self.update_count)
        next_vals = [self.q_values[next_state][(a, c)] for a in self.get_possible_actions(next_state) for c in self.state_transitions[next_state][a]] or [0]
        target = reward + self.gamma * max(next_vals)
        self.q_values[state][(action, next_char)] += alpha * (target - self.q_values[state][(action, next_char)])

# Generator class
class CredentialGeneratorMDP:
    def __init__(self, csv_path: str, wordlist_path: str,
                 user_include_char: bool, user_include_num: bool, user_include_sym: bool,
                 user_length: int,
                 pass_include_char: bool, pass_include_num: bool, pass_include_sym: bool,
                 pass_length: int):
        self.web_text = ""
        try:
            self.web_text = load_web_text(csv_path)
        except Exception:
            pass
        self.wordlists = []
        try:
            self.wordlists = load_wordlist(wordlist_path)
        except Exception:
            pass
        self.user_include_char = user_include_char
        self.user_include_num = user_include_num
        self.user_include_sym = user_include_sym
        self.pass_include_char = pass_include_char
        self.pass_include_num = pass_include_num
        self.pass_include_sym = pass_include_sym
        # Swap MDP roles to favor digits in usernames
        self.username_mdp = CredentialMDP(order=4)
        self.password_mdp = CredentialMDP(order=3)
        self.min_username_length = int(user_length)
        self.min_password_length = int(pass_length)
        self.username_symbols = set("!@#$%^&*()-_=+[]{}|;:'\".<>?/~`")
        self.password_symbols = set(self.username_symbols)

    def allowed_username_char(self, ch: str) -> bool:
        if ch.isalpha() and not self.user_include_char:
            return False
        if ch.isdigit() and not self.user_include_num:
            return False
        if ch in self.username_symbols and not self.user_include_sym:
            return False
        return True

    def allowed_password_char(self, ch: str) -> bool:
        if ch.isalpha() and not self.pass_include_char:
            return False
        if ch.isdigit() and not self.pass_include_num:
            return False
        if ch in self.password_symbols and not self.pass_include_sym:
            return False
        return True

    def get_allowed_username_chars(self) -> str:
        s = ''
        if self.user_include_char:
            s += 'abcdefghijklmnopqrstuvwxyz'
        if self.user_include_num:
            s += '0123456789'
        if self.user_include_sym:
            s += ''.join(self.username_symbols)
        return s

    def get_allowed_password_chars(self) -> str:
        s = ''
        if self.pass_include_char:
            s += 'abcdefghijklmnopqrstuvwxyz'
        if self.pass_include_num:
            s += '0123456789'
        if self.pass_include_sym:
            s += ''.join(self.password_symbols)
        return s

    def preprocess_text(self, text: str) -> List[str]:
        words = re.findall(r'\w+', text.lower())
        return [w for w in words if len(w) >= 4]

    def build_state_transitions(self):
        base = set(self.preprocess_text(self.web_text))
        if self.wordlists:
            base |= set(self.wordlists)
        # Username transitions
        for word in base:
            for i in range(len(word) - self.username_mdp.order):
                candidate = word[i + self.username_mdp.order]
                if not self.allowed_username_char(candidate):
                    continue
                prefix = word[i:i + self.username_mdp.order]
                state_sub = ''.join('#' if ch in self.username_symbols else ch for ch in prefix)
                state = f"username_{state_sub}"
                self.username_mdp.state_transitions[state][candidate].add(candidate)
                if i == 0 and all(self.allowed_username_char(ch) for ch in prefix):
                    self.username_mdp.initial_states.append(state)
        # Password transitions
        pwd_base = {w for w in base if len(w) >= 8 or w.isdigit()}
        for word in pwd_base:
            for i in range(len(word) - self.password_mdp.order):
                candidate = word[i + self.password_mdp.order]
                if not self.allowed_password_char(candidate):
                    continue
                prefix = word[i:i + self.password_mdp.order]
                state_sub = ''.join('#' if ch in self.password_symbols else ch for ch in prefix)
                state = f"password_{state_sub}"
                self.password_mdp.state_transitions[state][candidate].add(candidate)
                if i == 0 and all(self.allowed_password_char(ch) for ch in prefix):
                    self.password_mdp.initial_states.append(state)

    def generate_credential(self) -> Tuple[str, str]:
        # Generate username using password-style MDP for more digits
        state = random.choice(self.username_mdp.initial_states)
        username = state.split('_', 1)[1]
        chars = self.get_allowed_username_chars()
        while len(username) < self.min_username_length:
            action, nxt = self.username_mdp.choose_action(state)
            if not action:
                nxt = random.choice(chars)
            username += nxt
            next_state_sub = ''.join('#' if ch in self.username_symbols else ch for ch in username[-self.username_mdp.order:])
            next_state = f"username_{next_state_sub}"
            r = self.username_mdp.get_reward(state, action or nxt, nxt)
            self.username_mdp.update_q_value(state, action or nxt, nxt, next_state, r)
            state = next_state
        # Generate password using username-style MDP for variability
        state = random.choice(self.password_mdp.initial_states)
        password = state.split('_', 1)[1]
        chars = self.get_allowed_password_chars()
        while len(password) < self.min_password_length:
            action, nxt = self.password_mdp.choose_action(state)
            if not action:
                nxt = random.choice(chars)
            password += nxt
            next_state_sub = ''.join('#' if ch in self.password_symbols else ch for ch in password[-self.password_mdp.order:])
            next_state = f"password_{next_state_sub}"
            r = self.password_mdp.get_reward(state, action, nxt)
            self.password_mdp.update_q_value(state, action, nxt, next_state, r)
            state = next_state
        return username, password

    def generate_credentials(self, count: Union[int, str] = 10) -> List[Tuple[str, str]]:
        count = int(count)
        self.build_state_transitions()
        creds: List[Tuple[str, str]] = []
        for _ in range(count):
            if stop_generation:
                break
            creds.append(self.generate_credential())
        return creds

# Main driver
if __name__ == "__main__":
    site_list_csv_path = "site_list.csv"
    csv_path = "web_text.csv"
    wordlist_path = "wordlist.txt"
    urls = load_urls_from_csv(site_list_csv_path)
    scraper = WebScraper(urls)
    scraper.generate_csv(csv_path)
    nlp_subroutine(csv_path)
    generator = CredentialGeneratorMDP(
        csv_path, wordlist_path,
        user_include_char=True, user_include_num=True, user_include_sym=True,
        user_length=6,
        pass_include_char=True, pass_include_num=True, pass_include_sym=True,
        pass_length=12
    )
    creds = generator.generate_credentials(15)
    print("\nGenerated Credentials:")
    for u, p in creds:
        print(f"Username: {u}, Password: {p}")

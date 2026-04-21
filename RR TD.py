import pygame
import random
import math
import sys
import pandas as pd

# ------------------------------------------------------------
# FILE PATHS
# ------------------------------------------------------------
DATA_FILES = [
    r"D:\RDTS\US-and-Canada_aggregated_data_up_to_week_of-2026-03-28.csv",
    r"D:\RDTS\Asia-Pacific_aggregated_data_up_to_week_of-2026-03-28.csv",
    r"D:\RDTS\Europe-Central-Asia_aggregated_data_up_to_week_of-2026-03-28.csv",
]

# ------------------------------------------------------------
# COUNTRIES TO USE
# ------------------------------------------------------------
SELECTED_COUNTRIES = [
    "France",
    "Japan",
    "Thailand",
    "Canada",
    "India",
    "United States",
]

# ------------------------------------------------------------
# EXTRA TOURISM FEATURES
# ------------------------------------------------------------
TOURISM_FEATURES = {
    "France":         {"attractiveness": 0.92, "cost": 0.76, "social_media": 0.86, "preferred_by": "luxury"},
    "Japan":          {"attractiveness": 0.90, "cost": 0.72, "social_media": 0.88, "preferred_by": "luxury"},
    "Thailand":       {"attractiveness": 0.84, "cost": 0.34, "social_media": 0.80, "preferred_by": "budget"},
    "Canada":         {"attractiveness": 0.74, "cost": 0.70, "social_media": 0.68, "preferred_by": "family"},
    "India":          {"attractiveness": 0.78, "cost": 0.22, "social_media": 0.72, "preferred_by": "budget"},
    "United States":  {"attractiveness": 0.88, "cost": 0.82, "social_media": 0.90, "preferred_by": "family"},
}

# ------------------------------------------------------------
# SEGMENTS AND REGIONS
# ------------------------------------------------------------
SEGMENT_COLORS = {
    "budget":    (230, 140, 30),
    "luxury":    (220, 80, 160),
    "adventure": (80, 190, 80),
    "family":    (70, 170, 230),
}

SEGMENT_WEIGHTS = {
    "budget": {
        "alpha": 0.18, "beta": 0.24, "gamma": 0.10, "delta": 0.07,
        "eta": 0.30, "theta": 0.04, "epsilon": 0.03, "zeta": 0.04
    },
    "luxury": {
        "alpha": 0.24, "beta": 0.10, "gamma": 0.08, "delta": 0.08,
        "eta": 0.15, "theta": 0.12, "epsilon": 0.10, "zeta": 0.13
    },
    "adventure": {
        "alpha": 0.25, "beta": 0.09, "gamma": 0.08, "delta": 0.10,
        "eta": 0.20, "theta": 0.08, "epsilon": 0.07, "zeta": 0.13
    },
    "family": {
        "alpha": 0.18, "beta": 0.16, "gamma": 0.12, "delta": 0.12,
        "eta": 0.35, "theta": 0.03, "epsilon": 0.02, "zeta": 0.02
    },
}

HOME_REGIONS = {
    "Europe":      {"lat": 50.0, "lon": 10.0},
    "Americas":    {"lat": 40.0, "lon": -95.0},
    "AsiaPacific": {"lat": 15.0, "lon": 110.0},
    "Africa":      {"lat": 0.0,  "lon": 20.0},
    "MiddleEast":  {"lat": 25.0, "lon": 45.0},
}

HOME_REGION_WEIGHTS = [
    ("Europe", 0.24),
    ("Americas", 0.20),
    ("AsiaPacific", 0.28),
    ("Africa", 0.12),
    ("MiddleEast", 0.16),
]

# ------------------------------------------------------------
# VISUAL SETTINGS
# ------------------------------------------------------------
WHITE      = (255, 255, 255)
BLACK      = (20, 20, 20)
OCEAN      = (30, 80, 140)
GREEN      = (60, 180, 75)
RED        = (210, 40, 40)
YELLOW     = (255, 210, 40)
DARK_GRAY  = (80, 80, 80)
TEXT_LIGHT = (200, 220, 255)
TEXT_DIM   = (100, 130, 170)

WIDTH, HEIGHT = 1280, 780
FPS = 60
TOURIST_SPEED = 2.0
BASE_STAY_TICKS = 120
ARRIVAL_EVERY = 35
MAX_TOURISTS = 180
FESTIVAL_DURATION = 500
DISASTER_DURATION = 380

DISPLAY_POSITIONS = [
    (180, 160),
    (540, 140),
    (900, 180),
    (190, 540),
    (560, 560),
    (930, 520),
]

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def clamp01(x):
    return max(0.0, min(1.0, x))

def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def lerp_color(c1, c2, t):
    t = clamp01(t)
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def move_toward(pos, target, speed):
    dx = target[0] - pos[0]
    dy = target[1] - pos[1]
    d = math.hypot(dx, dy)
    if d == 0 or d < speed:
        return target
    return (pos[0] + dx / d * speed, pos[1] + dy / d * speed)

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def weighted_choice_from_pairs(pairs):
    total = sum(w for _, w in pairs)
    if total <= 0:
        return random.choice([k for k, _ in pairs])
    r = random.uniform(0, total)
    cum = 0.0
    for key, weight in pairs:
        cum += weight
        if cum >= r:
            return key
    return random.choice([k for k, _ in pairs])

def normalize_country_name(name):
    return str(name).strip().lower()

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------
def load_country_data():
    frames = []

    for file in DATA_FILES:
        print(f"\nReading file: {file}")
        df = pd.read_csv(file)
        print("Rows:", len(df))
        print("Columns:", list(df.columns))
        frames.append(df)

    all_df = pd.concat(frames, ignore_index=True)
    all_df["COUNTRY"] = all_df["COUNTRY"].astype(str).str.strip()
    all_df["WEEK"] = pd.to_datetime(all_df["WEEK"], errors="coerce")
    all_df = all_df.dropna(subset=["COUNTRY", "WEEK"])

    agg = all_df.groupby("COUNTRY", as_index=False).agg({
        "EVENTS": "sum",
        "FATALITIES": "sum",
        "POPULATION_EXPOSURE": "sum",
        "CENTROID_LATITUDE": "mean",
        "CENTROID_LONGITUDE": "mean"
    })

    agg["risk_raw"] = (
        agg["EVENTS"].fillna(0) * 1.0 +
        agg["FATALITIES"].fillna(0) * 3.0 +
        agg["POPULATION_EXPOSURE"].fillna(0) / 100000.0
    )

    min_risk = agg["risk_raw"].min()
    max_risk = agg["risk_raw"].max()

    if max_risk > min_risk:
        agg["risk"] = (agg["risk_raw"] - min_risk) / (max_risk - min_risk)
    else:
        agg["risk"] = 0.0

    result = {}
    for _, row in agg.iterrows():
        key = normalize_country_name(row["COUNTRY"])
        result[key] = {
            "country_name": str(row["COUNTRY"]).strip(),
            "lat": float(row["CENTROID_LATITUDE"]),
            "lon": float(row["CENTROID_LONGITUDE"]),
            "events": float(row["EVENTS"]),
            "fatalities": float(row["FATALITIES"]),
            "population_exposure": float(row["POPULATION_EXPOSURE"]),
            "risk": float(row["risk"]),
        }

    print("\nAvailable countries:")
    print(sorted([v["country_name"] for v in result.values()])[:120])

    return result

def build_sim_countries():
    base_data = load_country_data()
    sim_countries = []

    pos_index = 0
    for country_name in SELECTED_COUNTRIES:
        key = normalize_country_name(country_name)

        if key not in base_data:
            print(f"Warning: {country_name} not found in dataset, skipped.")
            continue

        if country_name not in TOURISM_FEATURES:
            print(f"Warning: {country_name} missing tourism features, skipped.")
            continue

        if pos_index >= len(DISPLAY_POSITIONS):
            break

        row = base_data[key]
        tourism = TOURISM_FEATURES[country_name]

        sim_countries.append({
            "name": country_name,
            "pos": DISPLAY_POSITIONS[pos_index],
            "lat": row["lat"],
            "lon": row["lon"],
            "capacity": 10 + int(max(0, 12 - row["risk"] * 8)),
            "attractiveness": tourism["attractiveness"],
            "cost": tourism["cost"],
            "risk": row["risk"],
            "social_media": tourism["social_media"],
            "preferred_by": tourism["preferred_by"],
            "events": row["events"],
            "fatalities": row["fatalities"],
        })
        pos_index += 1

    if len(sim_countries) == 0:
        raise ValueError("No selected countries were found. Check country names in the CSV files.")

    print("\nCountries used in simulation:")
    for c in sim_countries:
        print(c["name"])

    return sim_countries

# ------------------------------------------------------------
# COUNTRY CLASS
# ------------------------------------------------------------
class Country:
    RADIUS = 48

    def __init__(self, data):
        self.name = data["name"]
        self.pos = data["pos"]
        self.lat = data["lat"]
        self.lon = data["lon"]
        self.capacity = data["capacity"]
        self.attractiveness = data["attractiveness"]
        self.cost = data["cost"]
        self.risk = data["risk"]
        self.social_media = data["social_media"]
        self.preferred_by = data["preferred_by"]
        self.events = data["events"]
        self.fatalities = data["fatalities"]

        self.visitors = 0
        self.previous_arrivals = 0
        self.popularity = 0.0
        self.overcrowded = False
        self.festival = False
        self.disaster = False
        self.fest_timer = 0
        self.dis_timer = 0
        self._pulse = 0.0

    @property
    def effective_capacity(self):
        if self.festival:
            return max(1, int(self.capacity * 1.35))
        if self.disaster:
            return max(1, int(self.capacity * 0.45))
        return self.capacity

    def update(self, max_arrivals):
        self._pulse = (self._pulse + 0.07) % (2 * math.pi)

        if self.festival:
            self.fest_timer -= 1
            if self.fest_timer <= 0:
                self.festival = False

        if self.disaster:
            self.dis_timer -= 1
            if self.dis_timer <= 0:
                self.disaster = False

        self.overcrowded = self.visitors > self.effective_capacity
        self.popularity = math.log(self.previous_arrivals + 1) / math.log(max(max_arrivals, 1) + 1)

    def crowding_ratio(self):
        return clamp01(self.visitors / max(self.effective_capacity, 1))

    def status_color(self):
        if self.disaster:
            return DARK_GRAY
        if self.festival:
            return YELLOW
        if self.overcrowded:
            t = 0.5 + 0.5 * math.sin(self._pulse * 3)
            return lerp_color(RED, (255, 80, 80), t)
        fill = self.crowding_ratio()
        return lerp_color(GREEN, RED, fill)

    def draw(self, surf, font_sm, font_tiny):
        cx, cy = self.pos
        col = self.status_color()

        ring_r = self.RADIUS + 6
        if self.overcrowded:
            ring_col = (255, 70, 70)
        elif self.festival:
            ring_col = (255, 230, 50)
        elif self.disaster:
            ring_col = (120, 120, 120)
        else:
            ring_col = (col[0] // 2, col[1] // 2, col[2] // 2)

        pygame.draw.circle(surf, ring_col, (cx, cy), ring_r, 2)
        pygame.draw.circle(surf, col, (cx, cy), self.RADIUS)
        pygame.draw.circle(surf, WHITE, (cx, cy), self.RADIUS, 2)

        label = font_sm.render(self.name, True, WHITE)
        surf.blit(label, (cx - label.get_width() // 2, cy - self.RADIUS - 26))

        status = f"{self.visitors}/{self.effective_capacity}"
        slabel = font_tiny.render(status, True, WHITE)
        surf.blit(slabel, (cx - slabel.get_width() // 2, cy - 10))

        risk_label = font_tiny.render(f"risk {self.risk:.2f}", True, WHITE)
        surf.blit(risk_label, (cx - risk_label.get_width() // 2, cy + 8))

# ------------------------------------------------------------
# TOURIST CLASS
# ------------------------------------------------------------
class Tourist:
    RADIUS = 5

    def __init__(self, countries):
        self.segment = random.choice(["budget", "luxury", "adventure", "family"])
        self.color = SEGMENT_COLORS[self.segment]

        self.home_region = weighted_choice_from_pairs(HOME_REGION_WEIGHTS)
        self.home_lat = HOME_REGIONS[self.home_region]["lat"]
        self.home_lon = HOME_REGIONS[self.home_region]["lon"]

        self.weights = SEGMENT_WEIGHTS[self.segment]
        self.memory = {}

        self.current_country = random.choice(countries)
        self.pos = [
            self.current_country.pos[0] + random.uniform(-8, 8),
            self.current_country.pos[1] + random.uniform(-8, 8),
        ]

        self.dest = self.pick_destination(countries, exclude_country=self.current_country)
        self.state = "traveling"
        self.stay_timer = 0
        self._trail = []

    def utility(self, country, max_distance_km, max_arrivals):
        w = self.weights

        attractiveness = clamp01(country.attractiveness)
        cost = clamp01(country.cost)
        crowding = clamp01(country.visitors / max(country.effective_capacity, 1))
        risk = clamp01(country.risk)

        d_km = haversine_km(self.home_lat, self.home_lon, country.lat, country.lon)
        distance = clamp01(d_km / max(max_distance_km, 1))

        popularity = math.log(country.previous_arrivals + 1) / math.log(max(max_arrivals, 1) + 1)
        popularity = clamp01(popularity)

        social_media = clamp01(country.social_media)
        memory = clamp01(self.memory.get(country.name, 0.0))

        u = (
            w["alpha"] * attractiveness
            - w["beta"] * cost
            - w["gamma"] * crowding
            - w["delta"] * risk
            - w["eta"] * distance
            + w["theta"] * popularity
            + w["epsilon"] * social_media
            + w["zeta"] * memory
        )

        if self.segment == country.preferred_by:
            u += 0.10
        if country.festival:
            u += 0.14
        if country.disaster:
            u -= 0.40
        if country.overcrowded:
            u -= 0.22

        return u

    def pick_destination(self, countries, exclude_country=None):
        options = countries
        if exclude_country is not None:
            options = [c for c in countries if c != exclude_country]

        if not options:
            return exclude_country

        max_arrivals = max((c.previous_arrivals for c in options), default=1)
        max_distance_km = max(
            haversine_km(self.home_lat, self.home_lon, c.lat, c.lon)
            for c in options
        )

        utilities = []
        for c in options:
            u = self.utility(c, max_distance_km, max_arrivals)
            score = math.exp(max(-6, min(6, 4.0 * u)))
            utilities.append((c, score))

        total = sum(score for _, score in utilities)
        if total <= 0:
            return random.choice(options)

        r = random.uniform(0, total)
        cum = 0.0
        for c, score in utilities:
            cum += score
            if cum >= r:
                return c

        return random.choice(options)

    def update_memory(self):
        if self.current_country is None:
            return

        crowd_penalty = clamp01(self.current_country.visitors / max(self.current_country.effective_capacity, 1))
        satisfaction = 1.0 - crowd_penalty

        if self.current_country.disaster:
            satisfaction *= 0.35
        if self.current_country.festival:
            satisfaction = min(1.0, satisfaction + 0.15)

        old_memory = self.memory.get(self.current_country.name, 0.0)
        self.memory[self.current_country.name] = clamp01(0.6 * old_memory + 0.4 * satisfaction)

    def update(self, countries):
        self._trail.append(tuple(self.pos))
        if len(self._trail) > 12:
            self._trail.pop(0)

        if self.dest is None:
            self.dest = self.pick_destination(countries, exclude_country=self.current_country)
            if self.dest is None:
                return

        if self.state == "traveling":
            target = self.dest.pos
            self.pos = list(move_toward(tuple(self.pos), target, TOURIST_SPEED))

            if dist(self.pos, target) < 5:
                self.state = "staying"
                self.current_country = self.dest
                self.pos[0] += random.uniform(-8, 8)
                self.pos[1] += random.uniform(-8, 8)
                self.stay_timer = BASE_STAY_TICKS + random.randint(-25, 25)

        elif self.state == "staying":
            self.pos[0] += random.uniform(-0.7, 0.7)
            self.pos[1] += random.uniform(-0.7, 0.7)
            self.stay_timer -= 1

            if self.stay_timer <= 0:
                self.update_memory()
                self.dest = self.pick_destination(countries, exclude_country=self.current_country)
                self.state = "traveling"

    def draw(self, surf):
        for i, pt in enumerate(self._trail):
            alpha = int(180 * (i / max(len(self._trail), 1)))
            r = max(1, self.RADIUS - 2)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
            surf.blit(s, (int(pt[0]) - r, int(pt[1]) - r))

        pygame.draw.circle(surf, self.color, (int(self.pos[0]), int(self.pos[1])), self.RADIUS)
        pygame.draw.circle(surf, WHITE, (int(self.pos[0]), int(self.pos[1])), self.RADIUS, 1)

# ------------------------------------------------------------
# SIMULATION CLASS
# ------------------------------------------------------------
class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Tourism Simulation Using Dataset")
        self.clock = pygame.time.Clock()

        self.font_lg = pygame.font.SysFont("segoeui", 22, bold=True)
        self.font_md = pygame.font.SysFont("segoeui", 16, bold=True)
        self.font_sm = pygame.font.SysFont("segoeui", 14, bold=True)
        self.font_tiny = pygame.font.SysFont("segoeui", 12)

        self.reset()

    def reset(self):
        sim_country_data = build_sim_countries()
        self.countries = [Country(d) for d in sim_country_data]
        self.tourists = []
        self.tick = 0
        self.paused = False
        self.log = []
        self.spawn_batch(16)

    def spawn_batch(self, n):
        for _ in range(n):
            if len(self.tourists) < MAX_TOURISTS:
                self.tourists.append(Tourist(self.countries))

    def trigger_festival(self):
        eligible = [c for c in self.countries if not c.festival and not c.disaster]
        if not eligible:
            return
        c = random.choice(eligible)
        c.festival = True
        c.fest_timer = FESTIVAL_DURATION
        self.log.insert(0, (f"Festival in {c.name}", self.tick))
        self.log = self.log[:6]

    def trigger_disaster(self):
        eligible = [c for c in self.countries if not c.festival and not c.disaster]
        if not eligible:
            return
        c = random.choice(eligible)
        c.disaster = True
        c.dis_timer = DISASTER_DURATION
        self.log.insert(0, (f"Disaster in {c.name}", self.tick))
        self.log = self.log[:6]

    def update(self):
        if self.paused:
            return

        self.tick += 1

        for c in self.countries:
            c.previous_arrivals = c.visitors
            c.visitors = 0

        for t in self.tourists:
            if t.state == "staying" and t.current_country is not None:
                t.current_country.visitors += 1

        max_arrivals = max((c.previous_arrivals for c in self.countries), default=1)
        for c in self.countries:
            c.update(max_arrivals)

        for t in self.tourists:
            t.update(self.countries)

        if self.tick % ARRIVAL_EVERY == 0:
            self.spawn_batch(2)

        if random.random() < 0.003:
            self.trigger_festival()

        if random.random() < 0.002:
            self.trigger_disaster()

    def draw_background(self):
        self.screen.fill(OCEAN)
        for x in range(0, WIDTH, 60):
            pygame.draw.line(self.screen, (35, 90, 150), (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, 60):
            pygame.draw.line(self.screen, (35, 90, 150), (0, y), (WIDTH, y), 1)

    def draw_panel(self):
        pw = 280
        px = WIDTH - pw
        panel = pygame.Surface((pw, HEIGHT), pygame.SRCALPHA)
        panel.fill((10, 20, 40, 220))
        self.screen.blit(panel, (px, 0))

        y = 18
        title = self.font_lg.render("Tourism Dataset Sim", True, TEXT_LIGHT)
        self.screen.blit(title, (px + 12, y))
        y += 34

        stats = [
            ("Tourists", str(len(self.tourists))),
            ("Staying", str(sum(1 for t in self.tourists if t.state == "staying"))),
            ("Overcrowded", str(sum(1 for c in self.countries if c.overcrowded))),
            ("Tick", str(self.tick)),
        ]

        for label, value in stats:
            lbl = self.font_tiny.render(label, True, TEXT_DIM)
            val = self.font_md.render(value, True, TEXT_LIGHT)
            self.screen.blit(lbl, (px + 12, y))
            self.screen.blit(val, (px + pw - val.get_width() - 12, y))
            y += 24

        y += 12
        for c in self.countries:
            name = self.font_tiny.render(c.name, True, TEXT_LIGHT)
            info = self.font_tiny.render(
                f"vis {c.visitors}/{c.effective_capacity}   risk {c.risk:.2f}",
                True, TEXT_DIM
            )
            self.screen.blit(name, (px + 12, y))
            self.screen.blit(info, (px + 12, y + 16))
            y += 40

        y += 10
        legend_title = self.font_tiny.render("Tourist segments", True, TEXT_DIM)
        self.screen.blit(legend_title, (px + 12, y))
        y += 18
        for seg, col in SEGMENT_COLORS.items():
            pygame.draw.circle(self.screen, col, (px + 20, y + 6), 6)
            txt = self.font_tiny.render(seg, True, TEXT_DIM)
            self.screen.blit(txt, (px + 34, y))
            y += 20

    def draw(self):
        self.draw_background()
        for c in self.countries:
            c.draw(self.screen, self.font_sm, self.font_tiny)
        for t in self.tourists:
            t.draw(self.screen)
        self.draw_panel()
        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self.reset()
                    elif event.key == pygame.K_f:
                        self.trigger_festival()
                    elif event.key == pygame.K_d:
                        self.trigger_disaster()

            self.update()
            self.draw()
            self.clock.tick(FPS)

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    Simulation().run()
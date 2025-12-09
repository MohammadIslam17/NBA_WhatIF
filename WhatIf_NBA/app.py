import os
import math
from datetime import date, datetime
import re
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
from nba_api.stats.endpoints import TeamDashboardByGeneralSplits, CommonPlayerInfo
from nba_api.stats.static import players as nba_players

st.set_page_config(
    page_title="NBA Daily Scoreboard",
    page_icon="🏀",
    layout="wide",
)

API_BASE = "https://api.balldontlie.io/v1"

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

API_KEY = os.getenv("BALLDONTLIE_API_KEY")
FANTASYNERDS_API_KEY = os.getenv("FANTASYNERDS_API_KEY")

NBA_TEAM_ID_BY_ABBR = {
    "ATL": 1610612737,
    "BOS": 1610612738,
    "CLE": 1610612739,
    "NOP": 1610612740,
    "CHI": 1610612741,
    "DAL": 1610612742,
    "DEN": 1610612743,
    "GSW": 1610612744,
    "HOU": 1610612745,
    "LAC": 1610612746,
    "LAL": 1610612747,
    "MIA": 1610612748,
    "MIL": 1610612749,
    "MIN": 1610612750,
    "BKN": 1610612751,
    "NYK": 1610612752,
    "ORL": 1610612753,
    "IND": 1610612754,
    "PHI": 1610612755,
    "PHX": 1610612756,
    "POR": 1610612757,
    "SAC": 1610612758,
    "SAS": 1610612759,
    "OKC": 1610612760,
    "TOR": 1610612761,
    "UTA": 1610612762,
    "MEM": 1610612763,
    "WAS": 1610612764,
    "DET": 1610612765,
    "CHA": 1610612766,
}

PLAYER_FALLBACK_TO_TEAM = {
    "giannis": "MIL",
    "joker": "DEN",
    "steph": "GSW",
}

def auth_headers():
    if not API_KEY:
        raise RuntimeError(
            "BALLDONTLIE_API_KEY is not set. "
            "Create a .env file with BALLDONTLIE_API_KEY=your_key_here."
        )
    return {"Authorization": API_KEY}

@st.cache_data(ttl=60)
def fetch_games_for_date(game_date: str):
    params = {
        "dates[]": game_date,
        "per_page": 100,
    }
    url = f"{API_BASE}/games"
    resp = requests.get(url, params=params, headers=auth_headers(), timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])


def format_status(game):
    raw_status = (game.get("status") or "").strip()
    period = game.get("period") or 0

    if raw_status.lower() == "final":
        return "Final"

    looks_like_time = "pm" in raw_status.lower() or "am" in raw_status.lower()
    looks_like_iso = "T" in raw_status and raw_status.endswith("Z")
    if period == 0 and (
        looks_like_time
        or looks_like_iso
        or raw_status.lower() in ("scheduled", "not started", "")
    ):
        return "Not started"

    if raw_status.lower() == "halftime":
        return "Halftime"

    if period > 0:
        quarter_names = {
            1: "1st Qtr",
            2: "2nd Qtr",
            3: "3rd Qtr",
            4: "4th Qtr",
        }
        return quarter_names.get(period, f"Q{period}")
    return raw_status or "Unknown"


def team_display_name(team):
    if not team:
        return "Unknown"
    abbr = team.get("abbreviation", "")
    name = team.get("name", "")
    return f"{abbr} {name}".strip()


def team_logo_url(team):
    if not team:
        return None
    abbr = (team.get("abbreviation") or "").upper()
    team_id = NBA_TEAM_ID_BY_ABBR.get(abbr)
    if not team_id:
        return None
    return f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg"


def season_str_from_int(season_year: int) -> str:
    return f"{season_year}-{str(season_year + 1)[-2:]}"


@st.cache_data(ttl=3600)
def get_team_season_stats_nba_api(team_abbr: str, season_year: int):
    team_abbr = team_abbr.upper()
    team_id = NBA_TEAM_ID_BY_ABBR.get(team_abbr)
    if not team_id:
        raise ValueError(f"No NBA.com team id mapping for abbr {team_abbr}")

    season_str = season_str_from_int(season_year)

    resp = TeamDashboardByGeneralSplits(
        team_id=team_id,
        season=season_str,
    )
    df = resp.get_data_frames()[0]
    row = df.iloc[0]
    gp = row["GP"] or 1 
    pts_tot = row["PTS"]
    reb_tot = row["REB"]
    ast_tot = row["AST"]
    fgm = row["FGM"]
    fga = row["FGA"]
    fg3m = row["FG3M"]
    fg3a = row["FG3A"]
    w = row["W"]
    l = row["L"]

    ppg = pts_tot / gp
    rpg = reb_tot / gp
    apg = ast_tot / gp
    two_m = fgm - fg3m
    two_a = fga - fg3a
    two_pct = two_m / two_a if two_a else None
    three_m = fg3m / gp
    three_pct = row.get("FG3_PCT", fg3m / fg3a if fg3a else None)

    return {
        "ppg": ppg,
        "rpg": rpg,
        "apg": apg,
        "two_made": two_m / gp if gp else 0,
        "two_pct": two_pct,
        "three_made": three_m,
        "three_pct": three_pct,
        "wins": w,
        "losses": l,
        "games": gp,
    }

@st.cache_data(ttl=300)
def get_current_team_injuries(team_abbr: str):
    if not FANTASYNERDS_API_KEY:
        return []
    try:
        url = "https://api.fantasynerds.com/v1/nba/injuries"
        params = {"apikey": FANTASYNERDS_API_KEY}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, dict):
            injuries = (
                data.get("injuries")
                or data.get("Injuries")
                or data.get("data")
                or []
            )
        elif isinstance(data, list):
            injuries = data
        else:
            injuries = []

        team_abbr = team_abbr.upper()
        team_injuries = []
        for entry in injuries:
            entry_team = (
                str(entry.get("team") or entry.get("team_code") or "")
                .strip()
                .upper()
            )
            if entry_team != team_abbr:
                continue

            team_injuries.append(entry)

        return team_injuries

    except Exception as e:
        st.warning(f"Couldn't fetch injury data for {team_abbr}: {e}")
        return []


def compute_injury_adjustment_for_team(team_abbr: str):
    entries = get_current_team_injuries(team_abbr)
    if not entries:
        return 0.0, []

    rating_delta = 0.0
    notes = []

    for inj in entries:
        name = inj.get("player") or inj.get("name") or "Unknown player"
        status_raw = inj.get("status") or inj.get("injury_status") or ""
        status = status_raw.lower()

        if "out" in status or "doubtful" in status:
            rating_delta -= 6.0
        elif "questionable" in status or "day-to-day" in status or "day to day" in status:
            rating_delta -= 3.0
        else:
            rating_delta -= 2.0

        notes.append(f"{name} ({status_raw or 'injury'})")

    return rating_delta, notes

def extract_player_name_candidates(raw_text: str):
    words = re.findall(r"[A-Za-z]+", raw_text.lower())
    candidates = set()
    for i in range(len(words) - 1):
        candidates.add(f"{words[i]} {words[i + 1]}")
    for i in range(len(words) - 2):
        candidates.add(f"{words[i]} {words[i + 1]} {words[i + 2]}")

    return list(candidates)


@st.cache_data(ttl=3600)
def resolve_player_team(player_name: str):
    lower = player_name.lower().strip()
    if lower in PLAYER_FALLBACK_TO_TEAM:
        return PLAYER_FALLBACK_TO_TEAM[lower].upper(), player_name.strip()

    query_name = player_name.title().strip()
    results = nba_players.find_players_by_full_name(query_name)
    if not results:
        return None, None

    results_sorted = sorted(results, key=lambda r: (not r.get("is_active", False)))
    player = results_sorted[0]
    player_id = player["id"]

    try:
        info = CommonPlayerInfo(player_id=player_id)
        df = info.get_data_frames()[0]
        row = df.iloc[0]
        team_abbr = row.get("TEAM_ABBREVIATION") or None
        if team_abbr:
            return team_abbr.upper(), player["full_name"]
    except Exception:
        pass

    return None, None


def _logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def compute_win_probabilities(
    game: dict,
    home_stats: dict,
    away_stats: dict,
    status_label: str,
    rating_adj_home: float = 0.0,
    rating_adj_away: float = 0.0,
    force_live: bool = False,
):
    """
    Return (home_prob, away_prob) between 0 and 1.

    - Before game: based only on team strength + home court (+ adjustments).
    - During game: also adjusts for score margin and how far into the game we are.
    - After game is final: 100% for the winner, 0% for the loser.
    - If force_live=True, treat as an in-game scenario even if status is 'Not started'
      (used for what-if scenarios where we modify the score).
    """

    home_score = game.get("home_team_score", 0)
    away_score = game.get("visitor_team_score", 0)
    period = game.get("period") or 0
    if status_label == "Final" and not force_live:
        if home_score > away_score:
            return 1.0, 0.0
        elif away_score > home_score:
            return 0.0, 1.0
        else:
            return 0.5, 0.5

    home_rating = home_stats["ppg"] + (home_stats["wins"] - home_stats["losses"]) * 1.5
    away_rating = away_stats["ppg"] + (away_stats["wins"] - away_stats["losses"]) * 1.5
    home_rating += 3.0
    home_rating += rating_adj_home
    away_rating += rating_adj_away

    rating_diff = home_rating - away_rating 
    margin = home_score - away_score       
    if status_label == "Not started" and not force_live:
        x = rating_diff / 10.0
    else:
        effective_period = period
        if force_live and effective_period == 0:
            effective_period = 4

        time_factor = {0: 0.0, 1: 0.25, 2: 0.5, 3: 0.75}.get(effective_period, 1.0)
        live_adjust = margin * time_factor * 0.8
        x = (rating_diff + live_adjust) / 10.0

    home_prob = _logistic(x)
    away_prob = 1.0 - home_prob
    return home_prob, away_prob


def parse_what_if_scenario(
    what_if_text: str,
    game: dict,
    home_abbr: str,
    away_abbr: str,
):
    raw_text = what_if_text.strip()
    text = raw_text.lower()

    home_score_delta = 0
    away_score_delta = 0
    home_rating_delta = 0.0
    away_rating_delta = 0.0
    explanations = []

    m = re.search(r'([+-]?\d+)\s*(?:points?|pts?)', text)
    if m:
        pts = int(m.group(1))

        if "home" in text and "away" not in text:
            home_score_delta, away_score_delta = pts, 0
            explanations.append(f"Applied +{pts} points to the home team.")
        elif "away" in text and "home" not in text:
            home_score_delta, away_score_delta = 0, pts
            explanations.append(f"Applied +{pts} points to the away team.")
        else:
            if pts >= 0:
                home_score_delta, away_score_delta = pts, 0
                explanations.append(f"Applied +{pts} points to the home team.")
            else:
                home_score_delta, away_score_delta = 0, -pts
                explanations.append(f"Applied +{-pts} points to the away team.")

    injury_keywords = ["out", "not playing", "injured", "injury", "ruled out"]
    if any(kw in text for kw in injury_keywords):
        affected_team = None
        candidates = extract_player_name_candidates(raw_text)
        for cand in candidates:
            team_for_player, resolved_name = resolve_player_team(cand)
            if not team_for_player:
                continue

            team_for_player = team_for_player.upper()
            home_abbr_u = home_abbr.upper()
            away_abbr_u = away_abbr.upper()

            if team_for_player == home_abbr_u:
                affected_team = "home"
                home_rating_delta -= 8.0 
            elif team_for_player == away_abbr_u:
                affected_team = "away"
                away_rating_delta -= 8.0

            if affected_team:
                explanations.append(
                    f"{resolved_name} is out in this scenario: lowered {affected_team} team strength."
                )
                break

        if affected_team is None:
            if "home" in text and "away" not in text:
                home_rating_delta -= 5.0
                affected_team = "home"
            elif "away" in text and "home" not in text:
                away_rating_delta -= 5.0
                affected_team = "away"

            if affected_team:
                explanations.append(
                    f"Injury mentioned for the {affected_team} team: lowered their team strength."
                )

    return home_score_delta, away_score_delta, home_rating_delta, away_rating_delta, explanations

if "view" not in st.session_state:
    st.session_state["view"] = "scoreboard" 
if "selected_game" not in st.session_state:
    st.session_state["selected_game"] = None
if "prob_history" not in st.session_state:
    st.session_state["prob_history"] = {}

with st.sidebar:
    st.subheader("Settings")
    selected_date = st.date_input(
        "Select date",
        value=date.today(),
        help="Pick which day's games to view",
    )

    auto_refresh = st.checkbox(
        "Auto-refresh scores (every 30 seconds)",
        value=True,
        help="Useful while games are live",
    )

    st.markdown("---")
    st.caption("Scores: balldontlie.io • Stats: nba_api / NBA.com")
    if FANTASYNERDS_API_KEY:
        st.caption("Injuries: external provider (factored into win probabilities)")
    else:
        st.caption("Injuries: not configured (set FANTASYNERDS_API_KEY in .env)")

game_date_str = selected_date.strftime("%Y-%m-%d")

def render_scoreboard():
    st.markdown(
        "<h1 style='text-align:center;'>🏀 NBA Daily Scoreboard</h1>",
        unsafe_allow_html=True,
    )

    if auto_refresh:
        st_autorefresh(interval=30 * 1000, key="nba-scoreboard-refresh")

    with st.spinner(f"Loading games for {game_date_str}..."):
        try:
            games = fetch_games_for_date(game_date_str)
        except Exception as e:
            st.error(f"Error fetching games: {e}")
            st.stop()

    if not games:
        st.info("No NBA games scheduled for this date.")
        st.stop()

    games_sorted = sorted(games, key=lambda g: g.get("date", ""))

    for game in games_sorted:
        home = game.get("home_team", {})
        away = game.get("visitor_team", {})
        home_score = game.get("home_team_score", 0)
        away_score = game.get("visitor_team_score", 0)

        status_label = format_status(game)
        season_year = game.get("season") or date.today().year

        col1, col2, col3, col4, col5 = st.columns([3, 3, 2, 2, 1])

        with col1:
            st.markdown("#### Home")
            home_logo = team_logo_url(home)
            if home_logo:
                st.image(home_logo, width=60)
            st.markdown(f"**{team_display_name(home)}**")

        with col2:
            st.markdown("#### Away")
            away_logo = team_logo_url(away)
            if away_logo:
                st.image(away_logo, width=60)
            st.markdown(f"**{team_display_name(away)}**")

        with col3:
            st.markdown("#### Score")
            st.markdown(f"**{home_score} - {away_score}**")

        with col4:
            st.markdown("#### Status")
            st.write(status_label)

        with col5:
            if st.button("View ➜", key=f"view_btn_{game['id']}"):
                st.session_state["selected_game"] = {
                    "game": game,
                    "season_year": season_year,
                }
                st.session_state["view"] = "game_detail"
                st.rerun()

        st.markdown("---")

def render_team_stats(col, team, stats, label, align="left"):
    with col:
        text_align = "left" if align == "left" else "right"

        two_pct_str = "" if stats["two_pct"] is None else f"{stats['two_pct']*100:.1f}%"
        three_pct_str = "" if stats["three_pct"] is None else f"{stats['three_pct']*100:.1f}%"

        logo_url = team_logo_url(team) or ""
        flex_direction = "row-reverse" if align == "right" else "row"

        card_html = f"""
        <div style="
            border-radius: 12px;
            padding: 16px 18px;
            margin-top: 8px;
            background-color: #111827;
            border: 1px solid #1f2937;
            text-align:{text_align};
        ">
          <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;
                      flex-direction:{flex_direction};">
            <div>
              <img src="{logo_url}" style="width:52px; height:52px; object-fit:contain;" />
            </div>
            <div>
              <div style="font-size:0.8rem; opacity:0.8;">{label} team</div>
              <div style="font-size:1.05rem; font-weight:600;">{team_display_name(team)}</div>
            </div>
          </div>
          <div style="font-size:0.9rem; line-height:1.5;">
            <div>Games played: <b>{stats['games']}</b></div>
            <div>Win–Loss: <b>{stats['wins']}-{stats['losses']}</b></div>
            <div>Points per game: <b>{stats['ppg']:.1f}</b></div>
            <div>Rebounds per game: <b>{stats['rpg']:.1f}</b></div>
            <div>Assists per game: <b>{stats['apg']:.1f}</b></div>
            <hr style="border:none; border-top:1px solid #1f2937; margin:8px 0;" />
            <div>
              2PT FGM per game: <b>{stats['two_made']:.1f}</b>,
              2PT FG%: <b>{two_pct_str}</b>
            </div>
            <div>
              3PT FGM per game: <b>{stats['three_made']:.1f}</b>,
              3PT FG%: <b>{three_pct_str}</b>
            </div>
          </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

def _go_back_to_scoreboard():
    st.session_state["view"] = "scoreboard"
    st.session_state["selected_game"] = None

def render_game_detail():
    info = st.session_state.get("selected_game")
    if not info:
        _go_back_to_scoreboard()
        st.rerun()

    if auto_refresh:
        st_autorefresh(interval=30 * 1000, key="nba-game-detail-refresh")

    game = info["game"]
    season_year = info["season_year"]
    game_id = game["id"]

    home = game["home_team"]
    away = game["visitor_team"]
    home_score = game.get("home_team_score", 0)
    away_score = game.get("visitor_team_score", 0)
    status_label = format_status(game)

    home_abbr = home["abbreviation"]
    away_abbr = away["abbreviation"]
    try:
        home_stats = get_team_season_stats_nba_api(home_abbr, season_year)
        away_stats = get_team_season_stats_nba_api(away_abbr, season_year)
    except Exception as e:
        st.error(f"Error fetching team stats from nba_api: {e}")
        return

    home_injury_adj, home_injury_notes = compute_injury_adjustment_for_team(home_abbr)
    away_injury_adj, away_injury_notes = compute_injury_adjustment_for_team(away_abbr)

    pre_home_prob, pre_away_prob = compute_win_probabilities(
        game,
        home_stats,
        away_stats,
        "Not started",
        rating_adj_home=home_injury_adj,
        rating_adj_away=away_injury_adj,
    )
    home_prob, away_prob = compute_win_probabilities(
        game,
        home_stats,
        away_stats,
        status_label,
        rating_adj_home=home_injury_adj,
        rating_adj_away=away_injury_adj,
    )

    st.button("← Back to scoreboard", on_click=_go_back_to_scoreboard)

    st.markdown(
        "<h2 style='text-align:center; margin-top: 0.5rem;'>Game Details</h2>",
        unsafe_allow_html=True,
    )

    col_head1, col_head2, col_head3 = st.columns([3, 2, 3])

    with col_head1:
        home_logo = team_logo_url(home) or ""
        home_html = f"""
        <div style='text-align:left;'>
          <div style='text-align:center; font-size:0.9rem; opacity:0.7; margin-bottom:4px;'>Home</div>
          <img src='{home_logo}' style='display:block; margin:auto; width:80px; height:80px; object-fit:contain; margin-bottom:4px;' />
          <div style='text-align:center; font-size:1.1rem; font-weight:600;'>{team_display_name(home)}</div>
        </div>
        """
        st.markdown(home_html, unsafe_allow_html=True)

    with col_head2:
        pre_home_pct = pre_home_prob * 100
        pre_away_pct = pre_away_prob * 100
        current_home_pct = home_prob * 100
        current_away_pct = away_prob * 100

        center_html = f"""
        <div style='text-align:center;'>
          <div style='font-size:0.9rem; opacity:0.7;'>Score</div>
          <div style='font-size:2rem; font-weight:700; margin:4px 0;'>{home_score} - {away_score}</div>
          <div style='font-size:0.95rem; margin-bottom:4px;'>{status_label}</div>

          <div style='font-size:0.9rem; opacity:0.7; margin-top:4px;'>Pre-game win probability </div>
          <div style='font-size:0.9rem;'>
            Home {pre_home_pct:.1f}% &nbsp;–&nbsp; Away {pre_away_pct:.1f}%
          </div>

          <div style='font-size:0.9rem; opacity:0.7; margin-top:8px;'>Current win probability </div>
          <div style='font-size:1rem; font-weight:600;'>
            Home {current_home_pct:.1f}% &nbsp;–&nbsp; Away {current_away_pct:.1f}%
          </div>

          <div style="margin-top:6px; border-radius:999px; overflow:hidden; background-color:#1f2937; height:16px; width:100%; display:flex;">
            <div style="width:{current_home_pct:.1f}%; background:linear-gradient(90deg,#2563eb,#3b82f6);"></div>
            <div style="width:{current_away_pct:.1f}%; background:linear-gradient(90deg,#f97316,#fb923c);"></div>
          </div>
          <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-top:4px;">
            <span>Home</span>
            <span>Away</span>
          </div>
        </div>
        """
        st.markdown(center_html, unsafe_allow_html=True)

    with col_head3:
        away_logo = team_logo_url(away) or ""
        away_html = f"""
        <div style='text-align:right;'>
          <div style='text-align:center; font-size:0.9rem; opacity:0.7; margin-bottom:4px;'>Away</div>
          <img src='{away_logo}' style='display:block; margin:auto; width:80px; height:80px; object-fit:contain; margin-bottom:4px;' />
          <div style='text-align:center; font-size:1.1rem; font-weight:600;'>{team_display_name(away)}</div>
        </div>
        """
        st.markdown(away_html, unsafe_allow_html=True)

    if home_injury_notes or away_injury_notes:
        st.markdown("#### Injuries factored into model")
        if home_injury_notes:
            st.markdown(f"**Home ({home_abbr})**")
            for note in home_injury_notes:
                st.caption(f"• {note}")
        if away_injury_notes:
            st.markdown(f"**Away ({away_abbr})**")
            for note in away_injury_notes:
                st.caption(f"• {note}")

    st.markdown("---")
    st.markdown("### What-if Scenario")

    what_if_text = st.text_input(
        "Describe a scenario (points related for in game, player realted for pre game)",
        key=f"whatif_{game_id}",
        help="We adjust the score and/or team strength and recompute win probability on top of current injuries.",
    )

    if what_if_text.strip():
        (
            home_delta,
            away_delta,
            home_rating_delta,
            away_rating_delta,
            explanations,
        ) = parse_what_if_scenario(what_if_text, game, home_abbr, away_abbr)

        if (
            home_delta == 0
            and away_delta == 0
            and abs(home_rating_delta) < 1e-9
            and abs(away_rating_delta) < 1e-9
        ):
            st.info(
                "I couldn't understand that scenario. "
                "Try things like 'home up by 5', 'away scores 8 points', or "
                "'Paolo Banchero is not playing'."
            )
        else:
            new_home_score = home_score + home_delta
            new_away_score = away_score + away_delta

            hypothetical_game = dict(game)
            hypothetical_game["home_team_score"] = new_home_score
            hypothetical_game["visitor_team_score"] = new_away_score

            total_home_adj = home_injury_adj + home_rating_delta
            total_away_adj = away_injury_adj + away_rating_delta

            what_if_home_prob, what_if_away_prob = compute_win_probabilities(
                hypothetical_game,
                home_stats,
                away_stats,
                status_label,
                rating_adj_home=total_home_adj,
                rating_adj_away=total_away_adj,
            )

            st.markdown(
                f"**What-if score:** Home {new_home_score} – Away {new_away_score}"
            )
            st.markdown(
                f"**What-if win probability:** "
                f"Home {what_if_home_prob*100:.1f}% – Away {what_if_away_prob*100:.1f}%"
            )

            if explanations:
                st.caption("Scenario adjustments applied:")
                for exp in explanations:
                    st.caption(f"• {exp}")
            if home_rating_delta or away_rating_delta:
                st.caption(
                    "Note: These what-if changes are on top of any real injuries already factored in."
                )

    st.markdown("---")
    st.markdown("### Team Season Averages")

    col_home, col_away = st.columns(2)
    render_team_stats(col_home, home, home_stats, "Home", align="left")
    render_team_stats(col_away, away, away_stats, "Away", align="right")

if st.session_state["view"] == "scoreboard":
    render_scoreboard()
else:
    render_game_detail()

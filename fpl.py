
import csv
import tkinter as tk
from tkinter import messagebox


# ============================================================
# PLAYER
# ============================================================

class Player:

    def __init__(
        self,
        id,
        name,
        price,
        team,
        position,
        next_fixture,
        next_fixture_difficulty,
        xg,
        total_points
    ):
        self.id = str(id)
        self.name = name
        self.price = float(price)
        self.team = team
        self.position = position.lower().strip()
        self.next_fixture = next_fixture
        self.next_fixture_difficulty = int(next_fixture_difficulty)
        self.xg = float(xg)
        self.total_points = int(total_points)

    def captain_score(self):
        return (
            self.xg * (6 - self.next_fixture_difficulty)
            + self.total_points * 0.1
        )

    def get_stats(self):

        return (
            f"PLAYER: {self.name.upper()}\n"
            f"------------------------------\n"
            f"Club: {self.team}\n"
            f"Position: {self.position.upper()}\n"
            f"Price: £{self.price:.1f}M\n"
            f"Total Points: {self.total_points}\n"
            f"Next Fixture: {self.next_fixture}\n"
            f"Fixture Difficulty: "
            f"{self.next_fixture_difficulty}/5\n"
            f"xG: {self.xg}\n"
            f"Captain Score: "
            f"{self.captain_score():.2f}"
        )


# ============================================================
# TEAM
# ============================================================

class Team:

    def __init__(self, name="My FPL Team"):

        self.teamname = name

        self.budget = 100.0
        self.teamvalue = 0.0

        self.allplayers = []

        self.starting11 = []
        self.bench = []

        self.captain = None
        self.vicecaptain = None

        self.triple_captain_active = False
        self.bench_boost_active = False

    # --------------------------------------------------------
    # Count position
    # --------------------------------------------------------

    def count_position(self, position):

        return sum(
            1
            for p in self.allplayers
            if p.position == position
        )

    # --------------------------------------------------------
    # Count club
    # --------------------------------------------------------

    def count_team(self, team):

        return sum(
            1
            for p in self.allplayers
            if p.team == team
        )

    # --------------------------------------------------------
    # Add player
    # --------------------------------------------------------

    def add_player(self, player):

        if len(self.allplayers) >= 15:
            return False, "Squad is already full."

        if any(
            p.id == player.id
            for p in self.allplayers
        ):
            return False, f"{player.name} is already in your squad."

        if self.count_team(player.team) >= 3:
            return False, (
                f"You can only have 3 players "
                f"from {player.team}."
            )

        position_limits = {
            "gk": 2,
            "def": 5,
            "mid": 5,
            "fwd": 3
        }

        if player.position not in position_limits:
            return False, "Invalid player position."

        if (
            self.count_position(player.position)
            >= position_limits[player.position]
        ):
            return False, (
                f"Maximum {position_limits[player.position]} "
                f"{player.position.upper()} players allowed."
            )

        if player.price > self.budget + 0.001:
            return False, (
                f"Insufficient funds for {player.name}.\n"
                f"Remaining budget: £{self.budget:.1f}M"
            )

        self.allplayers.append(player)

        self.teamvalue += player.price
        self.budget -= player.price

        self.budget = round(self.budget, 2)
        self.teamvalue = round(self.teamvalue, 2)

        return True, f"{player.name} added successfully."

    # --------------------------------------------------------
    # Remove player
    # --------------------------------------------------------

    def remove_player(self, player):

        if player not in self.allplayers:
            return False, "Player is not in your squad."

        self.allplayers.remove(player)

        self.budget += player.price
        self.teamvalue -= player.price

        self.budget = round(self.budget, 2)
        self.teamvalue = round(self.teamvalue, 2)

        if player in self.starting11:
            self.starting11.remove(player)

        if player in self.bench:
            self.bench.remove(player)

        if self.captain == player:
            self.captain = None

        if self.vicecaptain == player:
            self.vicecaptain = None

        return True, f"{player.name} removed."

    # --------------------------------------------------------
    # Transfer
    # --------------------------------------------------------

    def transfer_player(self, player_out, player_in):

        if player_out not in self.allplayers:
            return False, "Player OUT is not in your squad."

        if player_in in self.allplayers:
            return False, "Player IN is already in your squad."

        if player_out.id == player_in.id:
            return False, "Player OUT and Player IN must be different."

        # Calculate the squad state AFTER the transfer without
        # changing anything yet.
        new_players = [
            p for p in self.allplayers
            if p != player_out
        ]

        # FPL squad position limits.
        position_limits = {
            "gk": 2,
            "def": 5,
            "mid": 5,
            "fwd": 3
        }

        position_count = sum(
            1 for p in new_players
            if p.position == player_in.position
        )

        if player_in.position not in position_limits:
            return False, "Invalid player position."

        if position_count >= position_limits[player_in.position]:
            return False, (
                f"Maximum {position_limits[player_in.position]} "
                f"{player_in.position.upper()} players allowed."
            )

        # Club limit after removing OUT.
        club_count = sum(
            1 for p in new_players
            if p.team == player_in.team
        )

        if club_count >= 3:
            return False, (
                f"You can only have 3 players from "
                f"{player_in.team}."
            )

        # Money available = current budget + OUT player's price.
        available_budget = round(
            self.budget + player_out.price,
            2
        )

        if player_in.price > available_budget + 0.001:
            return False, (
                f"Insufficient funds for {player_in.name}.\n"
                f"Available budget after selling "
                f"{player_out.name}: £{available_budget:.1f}M"
            )

        # Save state before making the transfer.
        old_allplayers = self.allplayers.copy()
        old_starting = self.starting11.copy()
        old_bench = self.bench.copy()
        old_captain = self.captain
        old_vicecaptain = self.vicecaptain
        old_budget = self.budget
        old_teamvalue = self.teamvalue

        try:
            # Replace OUT with IN while preserving allplayers order.
            self.allplayers = [
                player_in if p == player_out else p
                for p in self.allplayers
            ]

            self.budget = round(
                self.budget + player_out.price - player_in.price,
                2
            )

            self.teamvalue = round(
                self.teamvalue - player_out.price + player_in.price,
                2
            )

            # Keep the player's role (Starting XI / Bench).
            self.starting11 = [
                player_in if p == player_out else p
                for p in self.starting11
            ]

            self.bench = [
                player_in if p == player_out else p
                for p in self.bench
            ]

            if self.captain == player_out:
                self.captain = player_in

            if self.vicecaptain == player_out:
                self.vicecaptain = player_in

            return True, (
                f"Transfer completed!\n\n"
                f"OUT 🔴: {player_out.name}\n"
                f"IN 🟢: {player_in.name}"
            )

        except Exception as e:
            # Complete rollback if anything unexpected happens.
            self.allplayers = old_allplayers
            self.starting11 = old_starting
            self.bench = old_bench
            self.captain = old_captain
            self.vicecaptain = old_vicecaptain
            self.budget = old_budget
            self.teamvalue = old_teamvalue

            return False, f"Transfer failed: {e}"
    # --------------------------------------------------------
    # Formation validation
    # --------------------------------------------------------

    def valid_formation(self, players):

        if len(players) != 11:
            return False

        gk = sum(
            p.position == "gk"
            for p in players
        )

        df = sum(
            p.position == "def"
            for p in players
        )

        md = sum(
            p.position == "mid"
            for p in players
        )

        fw = sum(
            p.position == "fwd"
            for p in players
        )

        return (
            gk == 1
            and 3 <= df <= 5
            and 2 <= md <= 5
            and 1 <= fw <= 3
        )

    # --------------------------------------------------------
    # Auto Starting XI
    # --------------------------------------------------------

    def set_optimal_squad(self):

        if len(self.allplayers) != 15:
            return False, "You need exactly 15 players."

        gks = sorted(
            [p for p in self.allplayers if p.position == "gk"],
            key=lambda p: p.total_points,
            reverse=True
        )

        defs = sorted(
            [p for p in self.allplayers if p.position == "def"],
            key=lambda p: p.total_points,
            reverse=True
        )

        mids = sorted(
            [p for p in self.allplayers if p.position == "mid"],
            key=lambda p: p.total_points,
            reverse=True
        )

        fwds = sorted(
            [p for p in self.allplayers if p.position == "fwd"],
            key=lambda p: p.total_points,
            reverse=True
        )

        if (
            len(gks) < 1
            or len(defs) < 3
            or len(mids) < 2
            or len(fwds) < 1
        ):
            return False, "Cannot create a valid Starting XI."

        formations = [
            (3, 4, 3),
            (3, 5, 2),
            (4, 3, 3),
            (4, 4, 2),
            (4, 5, 1),
            (5, 3, 2),
            (5, 4, 1)
        ]

        best_team = None
        best_points = -1

        for df_count, mid_count, fw_count in formations:

            if (
                len(defs) >= df_count
                and len(mids) >= mid_count
                and len(fwds) >= fw_count
            ):

                current = (
                    [gks[0]]
                    + defs[:df_count]
                    + mids[:mid_count]
                    + fwds[:fw_count]
                )

                points = sum(
                    p.total_points
                    for p in current
                )

                if points > best_points:

                    best_points = points
                    best_team = current

        if best_team is None:
            return False, "Could not find a valid formation."

        self.starting11 = best_team

        self.bench = [
            p
            for p in self.allplayers
            if p not in self.starting11
        ]

        self.set_best_captains()

        return True, "Starting XI created successfully."

    # --------------------------------------------------------
    # Captain / Vice Captain
    # --------------------------------------------------------

    def set_best_captains(self):

        if len(self.starting11) < 2:
            self.captain = None
            self.vicecaptain = None
            return

        sorted_players = sorted(
            self.starting11,
            key=lambda p: p.captain_score(),
            reverse=True
        )

        self.captain = sorted_players[0]
        self.vicecaptain = sorted_players[1]

    # --------------------------------------------------------
    # Swap starting player and bench player
    # --------------------------------------------------------

    def swap_players(self, starting_player, bench_player):

        if starting_player not in self.starting11:
            return False, "Player is not in Starting XI."

        if bench_player not in self.bench:
            return False, "Player is not on the bench."

        # Build the potential new XI first.
        new_starting = self.starting11.copy()
        starting_index = new_starting.index(starting_player)
        new_starting[starting_index] = bench_player

        # Do not change the real team unless the formation is valid.
        if not self.valid_formation(new_starting):
            return False, (
                "This swap would create an invalid formation."
            )

        bench_index = self.bench.index(bench_player)

        # Swap in place, preserving the exact positions.
        self.starting11[starting_index] = bench_player
        self.bench[bench_index] = starting_player

        # Captain / vice-captain follow the player.
        if self.captain == starting_player:
            self.captain = bench_player

        if self.vicecaptain == starting_player:
            self.vicecaptain = bench_player

        # Safety: ensure captain and vice-captain are still valid.
        if (
            self.captain not in self.starting11
            or self.vicecaptain not in self.starting11
            or self.captain == self.vicecaptain
        ):
            self.set_best_captains()

        return True, (
            f"{bench_player.name} moved into Starting XI.\n"
            f"{starting_player.name} moved to the bench."
        )
    # --------------------------------------------------------
    # Set Captain
    # --------------------------------------------------------

    def set_captain(self, player):

        if player not in self.starting11:
            return False, "Captain must be a Starting XI player."

        if player == self.vicecaptain:
            self.vicecaptain = self.captain

        self.captain = player

        return True, f"{player.name} is now Captain."

    # --------------------------------------------------------
    # Set Vice Captain
    # --------------------------------------------------------

    def set_vicecaptain(self, player):

        if player not in self.starting11:
            return False, (
                "Vice Captain must be a Starting XI player."
            )

        if player == self.captain:
            return False, (
                "Captain and Vice Captain must be different."
            )

        self.vicecaptain = player

        return True, (
            f"{player.name} is now Vice Captain."
        )

    # --------------------------------------------------------
    # Gameweek points
    # --------------------------------------------------------

    def calculate_gameweek_points(self):

        total = 0

        for player in self.starting11:

            points = player.total_points

            if player == self.captain:

                if self.triple_captain_active:
                    points *= 3
                else:
                    points *= 2

            total += points

        if self.bench_boost_active:

            for player in self.bench:
                total += player.total_points

        return total


# ============================================================
# CSV LOADER
# ============================================================

def load_players_from_csv(file_path):

    players = []
    seen_ids = set()

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            required_columns = {
                "id",
                "name",
                "price",
                "team",
                "position",
                "next_fixture",
                "next_fixture_difficulty",
                "xg",
                "total_points"
            }

            if not required_columns.issubset(
                set(reader.fieldnames or [])
            ):

                raise ValueError(
                    "CSV columns are incorrect."
                )

            for row in reader:

                player_id = str(row["id"])

                if player_id in seen_ids:
                    continue

                seen_ids.add(player_id)

                try:

                    player = Player(
                        id=row["id"],
                        name=row["name"],
                        price=row["price"],
                        team=row["team"],
                        position=row["position"],
                        next_fixture=row["next_fixture"],
                        next_fixture_difficulty=row[
                            "next_fixture_difficulty"
                        ],
                        xg=row["xg"],
                        total_points=row["total_points"]
                    )

                    players.append(player)

                except ValueError:
                    continue

    except FileNotFoundError:

        messagebox.showerror(
            "Error",
            "players.csv was not found.\n\n"
            "Put players.csv in the same folder "
            "as main.py."
        )

    except Exception as e:

        messagebox.showerror(
            "CSV Error",
            str(e)
        )

    return players


# ============================================================
# GUI
# ============================================================

class FPLApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "FPL Manager System"
        )

        self.root.geometry(
            "1100x720"
        )
        self.root.minsize(
            950,
            620
        )
        self._setup_modern_theme()

        self.database = load_players_from_csv(
            "players.csv"
        )

        self.my_team = Team()

        self.displayed_players = self.database

        self.create_main_gui()

        self.update_listbox(
            self.database
        )

        self.update_status()

    def _setup_modern_theme(self):
        self.colors = {
            "bg": "#0B1220",
            "panel": "#111827",
            "card": "#172033",
            "card2": "#1E293B",
            "text": "#F8FAFC",
            "muted": "#94A3B8",
            "accent": "#22C55E",
            "accent_hover": "#16A34A",
            "select": "#166534",
            "border": "#334155",
        }
        c = self.colors
        self.root.configure(bg=c["bg"])
        self.root.option_add("*Font", ("Segoe UI", 10))
        self.root.option_add("*Background", c["panel"])
        self.root.option_add("*Foreground", c["text"])
        self.root.option_add("*Label.background", c["panel"])
        self.root.option_add("*Label.foreground", c["text"])
        self.root.option_add("*Button.background", c["accent"])
        self.root.option_add("*Button.foreground", "white")
        self.root.option_add("*Button.activeBackground", c["accent_hover"])
        self.root.option_add("*Button.activeForeground", "white")
        self.root.option_add("*Button.relief", "flat")
        self.root.option_add("*Button.borderWidth", 0)
        self.root.option_add("*Entry.background", c["card2"])
        self.root.option_add("*Entry.foreground", c["text"])
        self.root.option_add("*Entry.insertBackground", c["text"])
        self.root.option_add("*Listbox.background", c["card2"])
        self.root.option_add("*Listbox.foreground", c["text"])
        self.root.option_add("*Listbox.selectBackground", c["select"])
        self.root.option_add("*Listbox.selectForeground", "white")
        self.root.option_add("*Listbox.borderWidth", 0)
        self.root.option_add("*Listbox.highlightThickness", 0)
        self.root.option_add("*Checkbutton.background", c["panel"])
        self.root.option_add("*Checkbutton.foreground", c["text"])
        self.root.option_add("*Checkbutton.selectColor", c["accent"])
        self.root.option_add("*OptionMenu.background", c["card2"])
        self.root.option_add("*OptionMenu.foreground", c["text"])
        self.root.option_add("*OptionMenu.activeBackground", c["card"])
        self.root.option_add("*OptionMenu.activeForeground", c["text"])
        self.root.option_add("*Labelframe.background", c["panel"])
        self.root.option_add("*Labelframe.foreground", c["muted"])
        self.root.option_add("*Labelframe.borderColor", c["border"])
        self.root.option_add("*Labelframe.borderWidth", 1)

    # ========================================================
    # MAIN GUI
    # ========================================================

    def create_main_gui(self):

        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

        search_frame = tk.Frame(
            self.root,
            bg=self.colors["bg"],
            pady=14
        )

        search_frame.pack(
            fill="x"
        )

        tk.Label(
            search_frame,
            text="SEARCH PLAYERS",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10, "bold")
        ).pack(
            side="left",
            padx=10
        )

        self.search_entry = tk.Entry(
            search_frame,
            font=("Segoe UI", 11),
            bg=self.colors["card2"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            bd=0
        )

        self.search_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )

        self.search_entry.bind(
            "<KeyRelease>",
            self.filter_players
        )

        # ----------------------------------------------------
        # Main area
        # ----------------------------------------------------

        main_frame = tk.Frame(
            self.root,
            bg=self.colors["bg"]
        )

        main_frame.pack(
            fill="both",
            expand=True,
            padx=10
        )

        # ----------------------------------------------------
        # Player list
        # ----------------------------------------------------

        list_frame = tk.LabelFrame(
            main_frame,
            text="  PLAYERS  ",
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10, "bold"),
            bd=1,
            relief="solid"
        )

        list_frame.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 10),
            bg=self.colors["card2"],
            fg=self.colors["text"],
            selectbackground=self.colors["select"],
            selectforeground="white",
            activestyle="none",
            exportselection=False
        )

        self.listbox.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        self.listbox.bind(
            "<<ListboxSelect>>",
            self.on_player_select
        )

        # ----------------------------------------------------
        # Right panel
        # ----------------------------------------------------

        right_frame = tk.Frame(
            main_frame,
            width=340,
            bg=self.colors["bg"]
        )

        right_frame.pack(
            side="right",
            fill="both",
            padx=(10, 0)
        )

        # ----------------------------------------------------
        # Player info
        # ----------------------------------------------------

        info_frame = tk.LabelFrame(
            right_frame,
            text="  PLAYER INFORMATION  ",
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10, "bold"),
            bd=1,
            relief="solid"
        )

        info_frame.pack(
            fill="both",
            expand=True
        )

        self.details_label = tk.Label(
            info_frame,
            text="Select a player",
            justify="left",
            anchor="nw",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Consolas", 10),
            padx=4
        )

        self.details_label.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        # ----------------------------------------------------
        # Buttons
        # ----------------------------------------------------

        tk.Button(
            right_frame,
            text="➕ Add Player",
            command=self.add_player
        ).pack(
            fill="x",
            pady=3
        )

        tk.Button(
            right_frame,
            text="🔄 Transfer",
            command=self.open_transfer_window
        ).pack(
            fill="x",
            pady=3
        )

        tk.Button(
            right_frame,
            text="👥 My Squad",
            command=self.open_squad_window
        ).pack(
            fill="x",
            pady=3
        )

        tk.Button(
            right_frame,
            text="👑 Captain / Vice Captain",
            command=self.open_captain_window
        ).pack(
            fill="x",
            pady=3
        )

        tk.Button(
            right_frame,
            text="⚡ Chips",
            command=self.open_chips_window
        ).pack(
            fill="x",
            pady=3
        )

        tk.Button(
            right_frame,
            text="🤖 Auto-Build",
            command=self.auto_build
        ).pack(
            fill="x",
            pady=3
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        self.status_label = tk.Label(
            self.root,
            text="",
            bg=self.colors["card"],
            fg=self.colors["accent"],
            font=("Segoe UI", 10, "bold"),
            pady=10
        )

        self.status_label.pack(
            fill="x",
            side="bottom"
        )

    # ========================================================
    # PLAYER SEARCH
    # ========================================================

    def filter_players(self, event=None):

        query = (
            self.search_entry
            .get()
            .lower()
            .strip()
        )

        filtered = [
            p
            for p in self.database
            if (
                query in p.name.lower()
                or query in p.team.lower()
            )
        ]

        self.update_listbox(
            filtered
        )

    # ========================================================
    # UPDATE LIST
    # ========================================================

    def update_listbox(self, players):

        self.listbox.delete(
            0,
            tk.END
        )

        self.displayed_players = players

        for player in players:

            self.listbox.insert(
                tk.END,
                (
                    f"{player.name} | "
                    f"{player.position.upper()} | "
                    f"£{player.price:.1f}M"
                )
            )

    # ========================================================
    # SELECTED PLAYER
    # ========================================================

    def get_selected_player(self):

        selection = self.listbox.curselection()

        if not selection:
            return None

        return self.displayed_players[
            selection[0]
        ]

    # ========================================================
    # PLAYER INFO
    # ========================================================

    def on_player_select(self, event=None):

        player = self.get_selected_player()

        if player:

            self.details_label.config(
                text=player.get_stats()
            )

    # ========================================================
    # ADD PLAYER
    # ========================================================

    def add_player(self):

        player = self.get_selected_player()

        if not player:

            messagebox.showwarning(
                "Warning",
                "Select a player first."
            )

            return

        success, msg = (
            self.my_team.add_player(player)
        )

        if success:

            messagebox.showinfo(
                "Success",
                msg
            )

        else:

            messagebox.showerror(
                "Error",
                msg
            )

        self.update_status()

    # ========================================================
    # STATUS
    # ========================================================

    def update_status(self):

        self.status_label.config(
            text=(
                f"Squad: "
                f"{len(self.my_team.allplayers)}/15"
                f"   |   "
                f"Budget: "
                f"£{self.my_team.budget:.1f}M"
                f"   |   "
                f"Value: "
                f"£{self.my_team.teamvalue:.1f}M"
            )
        )

    # ========================================================
    # AUTO BUILD
    # ========================================================

    def auto_build(self):

        self.my_team = Team()

        # ----------------------------------------------------
        # Separate positions
        # ----------------------------------------------------

        gks = [
            p for p in self.database
            if p.position == "gk"
        ]

        defs = [
            p for p in self.database
            if p.position == "def"
        ]

        mids = [
            p for p in self.database
            if p.position == "mid"
        ]

        fwds = [
            p for p in self.database
            if p.position == "fwd"
        ]

        if (
            len(gks) < 2
            or len(defs) < 5
            or len(mids) < 5
            or len(fwds) < 3
        ):

            messagebox.showerror(
                "Auto-Build Error",
                "Not enough players in CSV.\n\n"
                "Required:\n"
                "2 GK\n"
                "5 DEF\n"
                "5 MID\n"
                "3 FWD"
            )

            return

        # ----------------------------------------------------
        # Score players
        # ----------------------------------------------------

        def score(player):

            fixture_bonus = (
                6 - player.next_fixture_difficulty
            )

            return (
                player.total_points * 0.55
                + player.xg * 30
                + fixture_bonus * 4
            )

        gks.sort(
            key=score,
            reverse=True
        )

        defs.sort(
            key=score,
            reverse=True
        )

        mids.sort(
            key=score,
            reverse=True
        )

        fwds.sort(
            key=score,
            reverse=True
        )

        # ----------------------------------------------------
        # Start with cheapest legal players
        # ----------------------------------------------------

        selected = []

        selected += sorted(
            gks,
            key=lambda p: p.price
        )[:2]

        selected += sorted(
            defs,
            key=lambda p: p.price
        )[:5]

        selected += sorted(
            mids,
            key=lambda p: p.price
        )[:5]

        selected += sorted(
            fwds,
            key=lambda p: p.price
        )[:3]

        # ----------------------------------------------------
        # Add initial squad
        # ----------------------------------------------------

        for player in selected:

            self.my_team.add_player(
                player
            )

        # ----------------------------------------------------
        # Upgrade players if budget allows
        # ----------------------------------------------------

        for position_list, limit in [
            (gks, 2),
            (defs, 5),
            (mids, 5),
            (fwds, 3)
        ]:

            current_position = [
                p
                for p in self.my_team.allplayers
                if p in position_list
            ]

            for candidate in position_list:

                if candidate in self.my_team.allplayers:
                    continue

                if len(current_position) >= limit:
                    break

                # Find weakest player of same position
                weakest = min(
                    current_position,
                    key=score
                )

                if score(candidate) <= score(weakest):
                    continue

                price_difference = (
                    candidate.price
                    - weakest.price
                )

                if price_difference <= self.my_team.budget:

                    self.my_team.remove_player(
                        weakest
                    )

                    success, _ = (
                        self.my_team.add_player(
                            candidate
                        )
                    )

                    if success:

                        current_position.remove(
                            weakest
                        )

                        current_position.append(
                            candidate
                        )

                    else:

                        self.my_team.add_player(
                            weakest
                        )

        # ----------------------------------------------------
        # Verify
        # ----------------------------------------------------

        if len(self.my_team.allplayers) != 15:

            messagebox.showerror(
                "Auto-Build Error",
                (
                    f"Could not build 15 players.\n"
                    f"Selected: "
                    f"{len(self.my_team.allplayers)}/15"
                )
            )

            return

        success, msg = (
            self.my_team.set_optimal_squad()
        )

        if not success:

            messagebox.showerror(
                "Error",
                msg
            )

            return

        self.update_status()

        messagebox.showinfo(
            "Auto-Build",
            "Your squad has been built successfully!"
        )

        self.open_squad_window()

    # ========================================================
    # SQUAD WINDOW
    # ========================================================

    def open_squad_window(self):

        if len(self.my_team.allplayers) != 15:

            messagebox.showwarning(
                "Squad",
                "You need exactly 15 players first."
            )

            return

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "My Squad"
        )

        window.geometry(
            "650x600"
        )
        window.configure(
            bg=self.colors["bg"]
        )

        # ----------------------------------------------------
        # Starting XI
        # ----------------------------------------------------

        tk.Label(
            window,
            text="🟢 STARTING XI",
            font=("Arial", 14, "bold")
        ).pack(
            pady=10
        )

        starting_list = tk.Listbox(
            window,
            height=12,
            width=70,
            font=("Consolas", 10),
            bg=self.colors["card2"],
            fg=self.colors["text"],
            selectbackground=self.colors["select"],
            selectforeground="white",
            activestyle="none",
            exportselection=False,
            relief="flat",
            bd=0
        )

        starting_list.pack(
            padx=10
        )

        for player in self.my_team.starting11:

            role = ""

            if player == self.my_team.captain:
                role = " ⭐ CAPTAIN"

            elif player == self.my_team.vicecaptain:
                role = " ⭐ VICE"

            starting_list.insert(
                tk.END,
                (
                    f"{player.name:<22}"
                    f"{player.position.upper():<6}"
                    f"{player.total_points:<5}"
                    f"{role}"
                )
            )

        # ----------------------------------------------------
        # Bench
        # ----------------------------------------------------

        tk.Label(
            window,
            text="🪑 BENCH",
            font=("Arial", 14, "bold")
        ).pack(
            pady=10
        )

        bench_list = tk.Listbox(
            window,
            height=5,
            width=70,
            font=("Consolas", 10),
            bg=self.colors["card2"],
            fg=self.colors["text"],
            selectbackground=self.colors["select"],
            selectforeground="white",
            activestyle="none",
            exportselection=False,
            relief="flat",
            bd=0
        )

        bench_list.pack(
            padx=10
        )

        for player in self.my_team.bench:

            bench_list.insert(
                tk.END,
                (
                    f"{player.name:<22}"
                    f"{player.position.upper():<6}"
                    f"{player.total_points}"
                )
            )

        # ----------------------------------------------------
        # Swap button
        # ----------------------------------------------------

        def swap_selected():

            s = starting_list.curselection()
            b = bench_list.curselection()

            if not s or not b:

                messagebox.showwarning(
                    "Swap",
                    "Select one Starting XI player "
                    "and one Bench player."
                )

                return

            player_out = (
                self.my_team.starting11[s[0]]
            )

            player_in = (
                self.my_team.bench[b[0]]
            )

            try:
                success, msg = self.my_team.swap_players(
                    player_out,
                    player_in
                )
            except Exception as e:
                success = False
                msg = f"Unexpected swap error: {e}"

            if success:

                messagebox.showinfo(
                    "Swap",
                    msg
                )

                window.destroy()
                self.update_status()
                self.open_squad_window()

            else:

                messagebox.showerror(
                    "Swap Error",
                    msg
                )

        tk.Button(
            window,
            text="🔁 Swap Starting XI ↔ Bench",
            command=swap_selected
        ).pack(
            pady=10
        )

        # ----------------------------------------------------
        # Points
        # ----------------------------------------------------

        tk.Label(
            window,
            text=(
                f"Captain: "
                f"{self.my_team.captain.name if self.my_team.captain else '-'}"
                f"\n"
                f"Vice Captain: "
                f"{self.my_team.vicecaptain.name if self.my_team.vicecaptain else '-'}"
                f"\n\n"
                f"Estimated GW Points: "
                f"{self.my_team.calculate_gameweek_points()}"
            ),
            font=("Arial", 11, "bold")
        ).pack(
            pady=10
        )

    # ========================================================
    # TRANSFER WINDOW
    # ========================================================

    def open_transfer_window(self):

        if len(self.my_team.allplayers) == 0:

            messagebox.showwarning(
                "Transfer",
                "Your squad is empty."
            )

            return

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Transfer Player"
        )

        window.geometry(
            "600x500"
        )
        window.configure(
            bg=self.colors["bg"]
        )

        # ----------------------------------------------------
        # OUT
        # ----------------------------------------------------

        tk.Label(
            window,
            text="🔴 PLAYER OUT",
            font=("Arial", 12, "bold")
        ).pack(
            pady=5
        )

        out_list = tk.Listbox(
            window,
            height=8,
            width=65,
            bg=self.colors["card2"],
            fg=self.colors["text"],
            selectbackground=self.colors["select"],
            selectforeground="white",
            activestyle="none",
            exportselection=False,
            relief="flat",
            bd=0
        )

        out_list.pack()

        for player in self.my_team.allplayers:

            out_list.insert(
                tk.END,
                (
                    f"{player.name} | "
                    f"{player.position.upper()} | "
                    f"£{player.price:.1f}M"
                )
            )

        # ----------------------------------------------------
        # IN
        # ----------------------------------------------------

        tk.Label(
            window,
            text="🟢 PLAYER IN",
            font=("Arial", 12, "bold")
        ).pack(
            pady=5
        )

        search = tk.Entry(
            window,
            font=("Segoe UI", 10),
            bg=self.colors["card2"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            bd=0
        )

        search.pack(
            fill="x",
            padx=20
        )

        in_list = tk.Listbox(
            window,
            height=8,
            width=65,
            bg=self.colors["card2"],
            fg=self.colors["text"],
            selectbackground=self.colors["select"],
            selectforeground="white",
            activestyle="none",
            exportselection=False,
            relief="flat",
            bd=0
        )

        in_list.pack(
            padx=20
        )

        available = []

        def update_transfer_list(event=None):

            query = (
                search.get()
                .lower()
                .strip()
            )

            in_list.delete(
                0,
                tk.END
            )

            available.clear()

            for player in self.database:

                if player in self.my_team.allplayers:
                    continue

                if (
                    query in player.name.lower()
                    or query in player.team.lower()
                ):

                    available.append(
                        player
                    )

                    in_list.insert(
                        tk.END,
                        (
                            f"{player.name} | "
                            f"{player.position.upper()} | "
                            f"£{player.price:.1f}M"
                        )
                    )

        search.bind(
            "<KeyRelease>",
            update_transfer_list
        )

        update_transfer_list()

        # ----------------------------------------------------
        # Transfer
        # ----------------------------------------------------

        def do_transfer():

            out_selection = (
                out_list.curselection()
            )

            in_selection = (
                in_list.curselection()
            )

            if not out_selection or not in_selection:

                messagebox.showwarning(
                    "Transfer",
                    "Select Player OUT and Player IN."
                )

                return

            player_out = (
                self.my_team.allplayers[
                    out_selection[0]
                ]
            )

            player_in = (
                available[
                    in_selection[0]
                ]
            )

            try:
                success, msg = self.my_team.transfer_player(
                    player_out,
                    player_in
                )
            except Exception as e:
                success = False
                msg = f"Unexpected transfer error: {e}"

            if success:

                messagebox.showinfo(
                    "Transfer",
                    msg
                )

                self.update_status()

                window.destroy()

            else:

                messagebox.showerror(
                    "Transfer",
                    msg
                )

        tk.Button(
            window,
            text="🔄 MAKE TRANSFER",
            command=do_transfer
        ).pack(
            pady=15
        )

    # ========================================================
    # CAPTAIN WINDOW
    # ========================================================

    def open_captain_window(self):

        if len(self.my_team.starting11) != 11:

            messagebox.showwarning(
                "Captain",
                "Build your Starting XI first."
            )

            return

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Captain & Vice Captain"
        )

        window.geometry(
            "400x350"
        )
        window.configure(
            bg=self.colors["bg"]
        )

        tk.Label(
            window,
            text="👑 CAPTAIN",
            font=("Arial", 12, "bold")
        ).pack(
            pady=10
        )

        captain_var = tk.StringVar(
            value=self.my_team.captain.name
            if self.my_team.captain else ""
        )

        captain_menu = tk.OptionMenu(
            window,
            captain_var,
            *[
                p.name
                for p in self.my_team.starting11
            ]
        )

        captain_menu.pack()

        tk.Label(
            window,
            text="🥈 VICE CAPTAIN",
            font=("Arial", 12, "bold")
        ).pack(
            pady=10
        )

        vice_var = tk.StringVar(
            value=self.my_team.vicecaptain.name
            if self.my_team.vicecaptain else ""
        )

        vice_menu = tk.OptionMenu(
            window,
            vice_var,
            *[
                p.name
                for p in self.my_team.starting11
            ]
        )

        vice_menu.pack()

        def save():

            captain = next(
                p
                for p in self.my_team.starting11
                if p.name == captain_var.get()
            )

            vice = next(
                p
                for p in self.my_team.starting11
                if p.name == vice_var.get()
            )

            if captain == vice:

                messagebox.showerror(
                    "Error",
                    "Captain and Vice Captain "
                    "must be different."
                )

                return

            self.my_team.set_captain(
                captain
            )

            self.my_team.set_vicecaptain(
                vice
            )

            messagebox.showinfo(
                "Saved",
                (
                    f"Captain: {captain.name}\n"
                    f"Vice Captain: {vice.name}"
                )
            )

            window.destroy()

        tk.Button(
            window,
            text="💾 Save",
            command=save
        ).pack(
            pady=20
        )

    # ========================================================
    # CHIPS WINDOW
    # ========================================================

    def open_chips_window(self):

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "FPL Chips"
        )

        window.geometry(
            "350x300"
        )
        window.configure(
            bg=self.colors["bg"]
        )

        triple_var = tk.BooleanVar(
            value=self.my_team.triple_captain_active
        )

        bench_var = tk.BooleanVar(
            value=self.my_team.bench_boost_active
        )

        tk.Checkbutton(
            window,
            text="⚡ Triple Captain",
            variable=triple_var
        ).pack(
            pady=20
        )

        tk.Checkbutton(
            window,
            text="🪑 Bench Boost",
            variable=bench_var
        ).pack(
            pady=20
        )

        def save():

            self.my_team.triple_captain_active = (
                triple_var.get()
            )

            self.my_team.bench_boost_active = (
                bench_var.get()
            )

            messagebox.showinfo(
                "Chips",
                "Chip settings saved."
            )

            window.destroy()

        tk.Button(
            window,
            text="💾 Save",
            command=save
        ).pack(
            pady=20
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = FPLApp(
        root
    )

    root.mainloop()
